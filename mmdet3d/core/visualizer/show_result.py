import mmcv
import numpy as np
import trimesh
from os import path as osp


def _write_obj(points, out_filename):
    """Write points into ``obj`` format for meshlab visualization.

    Args:
        points (np.ndarray): Points in shape (N, dim).
        out_filename (str): Filename to be saved.
    """
    N = points.shape[0]
    fout = open(out_filename, 'w')
    for i in range(N):
        if points.shape[1] == 6:
            c = points[i, 3:].astype(int)
            fout.write(
                'v %f %f %f %d %d %d\n' %
                (points[i, 0], points[i, 1], points[i, 2], c[0], c[1], c[2]))

        else:
            fout.write('v %f %f %f\n' %
                       (points[i, 0], points[i, 1], points[i, 2]))
    fout.close()


def _write_oriented_bbox(scene_bbox, out_filename):
    """Export oriented (around Z axis) scene bbox to meshes.

    Args:
        scene_bbox(list[ndarray] or ndarray): xyz pos of center and
            3 lengths (dx,dy,dz) and heading angle around Z axis.
            Y forward, X right, Z upward. heading angle of positive X is 0,
            heading angle of positive Y is 90 degrees.
        out_filename(str): Filename.
    """

    def heading2rotmat(heading_angle):
        rotmat = np.zeros((3, 3))
        rotmat[2, 2] = 1
        cosval = np.cos(heading_angle)
        sinval = np.sin(heading_angle)
        rotmat[0:2, 0:2] = np.array([[cosval, -sinval], [sinval, cosval]])
        return rotmat

    def convert_oriented_box_to_trimesh_fmt(box):
        ctr = box[:3]
        lengths = box[3:6]
        trns = np.eye(4)
        trns[0:3, 3] = ctr
        trns[3, 3] = 1.0
        trns[0:3, 0:3] = heading2rotmat(box[6])
        box_trimesh_fmt = trimesh.creation.box(lengths, trns)
        return box_trimesh_fmt

    if len(scene_bbox) == 0:
        scene_bbox = np.zeros((1, 7))
    scene = trimesh.scene.Scene()
    for box in scene_bbox:
        scene.add_geometry(convert_oriented_box_to_trimesh_fmt(box))

    mesh_list = trimesh.util.concatenate(scene.dump())
    # save to obj file
    trimesh.io.export.export_mesh(mesh_list, out_filename, file_type='obj')

    return


def show_result(points, gt_bboxes, pred_bboxes, out_dir, filename, show=True):
    """Convert results into format that is directly readable for meshlab.

    Args:
        points (np.ndarray): Points.
        gt_bboxes (np.ndarray): Ground truth boxes.
        pred_bboxes (np.ndarray): Predicted boxes.
        out_dir (str): Path of output directory
        filename (str): Filename of the current frame.
        show (bool): Visualize the results online.
    """
    if show:
        from .open3d_vis import Visualizer

        vis = Visualizer(points)
        if pred_bboxes is not None:
            vis.add_bboxes(bbox3d=pred_bboxes)
        if gt_bboxes is not None:
            vis.add_bboxes(bbox3d=gt_bboxes, bbox_color=(0, 0, 1))
        vis.show()

    result_path = osp.join(out_dir, filename)
    mmcv.mkdir_or_exist(result_path)

    if points is not None:
        _write_obj(points, osp.join(result_path, f'{filename}_points.obj'))

    if gt_bboxes is not None:
        # bottom center to gravity center
        gt_bboxes[..., 2] += gt_bboxes[..., 5] / 2
        # the positive direction for yaw in meshlab is clockwise
        gt_bboxes[:, 6] *= -1
        _write_oriented_bbox(gt_bboxes,
                             osp.join(result_path, f'{filename}_gt.obj'))

    if pred_bboxes is not None:
        # bottom center to gravity center
        pred_bboxes[..., 2] += pred_bboxes[..., 5] / 2
        # the positive direction for yaw in meshlab is clockwise
        pred_bboxes[:, 6] *= -1
        _write_oriented_bbox(pred_bboxes,
                             osp.join(result_path, f'{filename}_pred.obj'))


def show_seg_result(points,
                    gt_seg,
                    pred_seg,
                    out_dir,
                    filename,
                    palette,
                    ignore_index=None,
                    show=False):
    """Convert results into format that is directly readable for meshlab.

    Args:
        points (np.ndarray): Points.
        gt_seg (np.ndarray): Ground truth segmentation mask.
        pred_seg (np.ndarray): Predicted segmentation mask.
        out_dir (str): Path of output directory
        filename (str): Filename of the current frame.
        palette (np.ndarray): Mapping between class labels and colors.
        ignore_index (int, optional): The label index to be ignored, e.g. \
            unannotated points. Defaults to None.
        show (bool, optional): Visualize the results online. Defaults to False.
    """
    '''
    # TODO: not sure how to draw colors online, maybe we need two frames?
    from .open3d_vis import Visualizer

    if show:
        vis = Visualizer(points)
        if pred_bboxes is not None:
            vis.add_bboxes(bbox3d=pred_bboxes)
        if gt_bboxes is not None:
            vis.add_bboxes(bbox3d=gt_bboxes, bbox_color=(0, 0, 1))
        vis.show()
    '''

    # filter out ignored points
    if gt_seg is not None and ignore_index is not None:
        if points is not None:
            points = points[gt_seg != ignore_index]
        if pred_seg is not None:
            pred_seg = pred_seg[gt_seg != ignore_index]
        gt_seg = gt_seg[gt_seg != ignore_index]

    if gt_seg is not None:
        gt_seg_color = palette[gt_seg]
    if pred_seg is not None:
        pred_seg_color = palette[pred_seg]

    result_path = osp.join(out_dir, filename)
    mmcv.mkdir_or_exist(result_path)

    if points is not None:
        _write_obj(points, osp.join(result_path, f'{filename}_points.obj'))

    if gt_seg is not None:
        gt_seg = np.concatenate([points[:, :3], gt_seg_color], axis=1)
        _write_obj(gt_seg, osp.join(result_path, f'{filename}_gt.obj'))

    if pred_seg is not None:
        pred_seg = np.concatenate([points[:, :3], pred_seg_color], axis=1)
        _write_obj(pred_seg, osp.join(result_path, f'{filename}_pred.obj'))
