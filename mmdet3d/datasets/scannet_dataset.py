import numpy as np
from os import path as osp

from mmdet3d.core import show_result, show_seg_result
from mmdet3d.core.bbox import DepthInstance3DBoxes
from mmdet.datasets import DATASETS
from .custom_3d import Custom3DDataset
from .custom_3d_seg import Custom3DSegDataset


@DATASETS.register_module()
class ScanNetDataset(Custom3DDataset):
    r"""ScanNet Dataset for Detection Task.

    This class serves as the API for experiments on the ScanNet Dataset.

    Please refer to the `github repo <https://github.com/ScanNet/ScanNet>`_
    for data downloading.

    Args:
        data_root (str): Path of dataset root.
        ann_file (str): Path of annotation file.
        pipeline (list[dict], optional): Pipeline used for data processing.
            Defaults to None.
        classes (tuple[str], optional): Classes used in the dataset.
            Defaults to None.
        modality (dict, optional): Modality to specify the sensor data used
            as input. Defaults to None.
        box_type_3d (str, optional): Type of 3D box of this dataset.
            Based on the `box_type_3d`, the dataset will encapsulate the box
            to its original format then converted them to `box_type_3d`.
            Defaults to 'Depth' in this dataset. Available options includes

            - 'LiDAR': Box in LiDAR coordinates.
            - 'Depth': Box in depth coordinates, usually for indoor dataset.
            - 'Camera': Box in camera coordinates.
        filter_empty_gt (bool, optional): Whether to filter empty GT.
            Defaults to True.
        test_mode (bool, optional): Whether the dataset is in test mode.
            Defaults to False.
    """
    CLASSES = ('cabinet', 'bed', 'chair', 'sofa', 'table', 'door', 'window',
               'bookshelf', 'picture', 'counter', 'desk', 'curtain',
               'refrigerator', 'showercurtrain', 'toilet', 'sink', 'bathtub',
               'garbagebin')

    def __init__(self,
                 data_root,
                 ann_file,
                 pipeline=None,
                 classes=None,
                 modality=None,
                 box_type_3d='Depth',
                 filter_empty_gt=True,
                 test_mode=False):
        super().__init__(
            data_root=data_root,
            ann_file=ann_file,
            pipeline=pipeline,
            classes=classes,
            modality=modality,
            box_type_3d=box_type_3d,
            filter_empty_gt=filter_empty_gt,
            test_mode=test_mode)

    def get_ann_info(self, index):
        """Get annotation info according to the given index.

        Args:
            index (int): Index of the annotation data to get.

        Returns:
            dict: annotation information consists of the following keys:

                - gt_bboxes_3d (:obj:`DepthInstance3DBoxes`): \
                    3D ground truth bboxes
                - gt_labels_3d (np.ndarray): Labels of ground truths.
                - pts_instance_mask_path (str): Path of instance masks.
                - pts_semantic_mask_path (str): Path of semantic masks.
        """
        # Use index to get the annos, thus the evalhook could also use this api
        info = self.data_infos[index]
        if info['annos']['gt_num'] != 0:
            gt_bboxes_3d = info['annos']['gt_boxes_upright_depth'].astype(
                np.float32)  # k, 6
            gt_labels_3d = info['annos']['class'].astype(np.long)
        else:
            gt_bboxes_3d = np.zeros((0, 6), dtype=np.float32)
            gt_labels_3d = np.zeros((0, ), dtype=np.long)

        # to target box structure
        gt_bboxes_3d = DepthInstance3DBoxes(
            gt_bboxes_3d,
            box_dim=gt_bboxes_3d.shape[-1],
            with_yaw=False,
            origin=(0.5, 0.5, 0.5)).convert_to(self.box_mode_3d)

        pts_instance_mask_path = osp.join(self.data_root,
                                          info['pts_instance_mask_path'])
        pts_semantic_mask_path = osp.join(self.data_root,
                                          info['pts_semantic_mask_path'])

        anns_results = dict(
            gt_bboxes_3d=gt_bboxes_3d,
            gt_labels_3d=gt_labels_3d,
            pts_instance_mask_path=pts_instance_mask_path,
            pts_semantic_mask_path=pts_semantic_mask_path)
        return anns_results

    def show(self, results, out_dir, show=True):
        """Results visualization.

        Args:
            results (list[dict]): List of bounding boxes results.
            out_dir (str): Output directory of visualization result.
            show (bool): Visualize the results online.
        """
        assert out_dir is not None, 'Expect out_dir, got none.'
        for i, result in enumerate(results):
            data_info = self.data_infos[i]
            pts_path = data_info['pts_path']
            file_name = osp.split(pts_path)[-1].split('.')[0]
            points = np.fromfile(
                osp.join(self.data_root, pts_path),
                dtype=np.float32).reshape(-1, 6)
            gt_bboxes = self.get_ann_info(i)['gt_bboxes_3d'].tensor
            pred_bboxes = result['boxes_3d'].tensor.numpy()
            show_result(points, gt_bboxes, pred_bboxes, out_dir, file_name,
                        show)


@DATASETS.register_module()
class ScanNetSegDataset(Custom3DSegDataset):
    r"""ScanNet Dataset for Semantic Segmentation Task.

    This class serves as the API for experiments on the ScanNet Dataset.

    Please refer to the `github repo <https://github.com/ScanNet/ScanNet>`_
    for data downloading.

    Args:
        data_root (str): Path of dataset root.
        ann_file (str): Path of annotation file.
        pipeline (list[dict], optional): Pipeline used for data processing.
            Defaults to None.
        classes (tuple[str], optional): Classes used in the dataset.
            Defaults to None.
        palette (list[list[int]], optional): The palette of segmentation map.
            Defaults to None.
        modality (dict, optional): Modality to specify the sensor data used
            as input. Defaults to None.
        test_mode (bool, optional): Whether the dataset is in test mode.
            Defaults to False.
        ignore_index (int, optional): The label index to be ignored, e.g. \
            unannotated points. If None is given, set to len(self.CLASSES).
            Defaults to None.
        scene_idxs (np.ndarray | str, optional): Precomputed index to load
            data. For scenes with many points, we may sample it several times.
            Defaults to None.
        label_weight (np.ndarray | str, optional): Precomputed weight to \
            balance loss calculation. If None is given, compute from data.
            Defaults to None.
    """
    CLASSES = ('wall', 'floor', 'cabinet', 'bed', 'chair', 'sofa', 'table',
               'door', 'window', 'bookshelf', 'picture', 'counter', 'desk',
               'curtain', 'refrigerator', 'showercurtrain', 'toilet', 'sink',
               'bathtub', 'otherfurniture')

    VALID_CLASS_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 24, 28,
                       33, 34, 36, 39)

    ALL_CLASS_IDS = tuple(range(41))

    PALETTE = [
        [174, 199, 232],
        [152, 223, 138],
        [31, 119, 180],
        [255, 187, 120],
        [188, 189, 34],
        [140, 86, 75],
        [255, 152, 150],
        [214, 39, 40],
        [197, 176, 213],
        [148, 103, 189],
        [196, 156, 148],
        [23, 190, 207],
        [247, 182, 210],
        [219, 219, 141],
        [255, 127, 14],
        [158, 218, 229],
        [44, 160, 44],
        [112, 128, 144],
        [227, 119, 194],
        [82, 84, 163],
    ]

    def __init__(self,
                 data_root,
                 ann_file,
                 pipeline=None,
                 classes=None,
                 palette=None,
                 modality=None,
                 test_mode=False,
                 ignore_index=None,
                 scene_idxs=None,
                 label_weight=None):

        super().__init__(
            data_root=data_root,
            ann_file=ann_file,
            pipeline=pipeline,
            classes=classes,
            palette=palette,
            modality=modality,
            test_mode=test_mode,
            ignore_index=ignore_index,
            scene_idxs=scene_idxs,
            label_weight=label_weight)

    def get_ann_info(self, index):
        """Get annotation info according to the given index.

        Args:
            index (int): Index of the annotation data to get.

        Returns:
            dict: annotation information consists of the following keys:

                - pts_semantic_mask_path (str): Path of semantic masks.
        """
        # Use index to get the annos, thus the evalhook could also use this api
        info = self.data_infos[index]

        pts_semantic_mask_path = osp.join(self.data_root,
                                          info['pts_semantic_mask_path'])

        anns_results = dict(pts_semantic_mask_path=pts_semantic_mask_path)
        return anns_results

    def show(self, results, out_dir, show=True):
        """Results visualization.

        Args:
            results (list[dict]): List of bounding boxes results.
            out_dir (str): Output directory of visualization result.
            show (bool): Visualize the results online.
        """
        assert out_dir is not None, 'Expect out_dir, got none.'
        for i, result in enumerate(results):
            data_info = self.data_infos[i]
            pts_path = data_info['pts_path']
            file_name = osp.split(pts_path)[-1].split('.')[0]
            points = np.fromfile(
                osp.join(self.data_root, pts_path),
                dtype=np.float32).reshape(-1, 6)
            sem_mask_path = data_info['pts_semantic_mask_path']
            gt_sem_mask = self.convert_to_label(
                osp.join(self.data_root, sem_mask_path))
            pred_sem_mask = result['semantic_mask'].numpy()
            show_seg_result(points, gt_sem_mask,
                            pred_sem_mask, out_dir, file_name,
                            np.array(self.PALETTE), self.ignore_index, show)

    def get_scene_idxs_and_label_weight(self, scene_idxs, label_weight):
        """Compute scene_idxs for data sampling and label weight for loss \
        calculation.

        We sample more times for scenes with more points. Label_weight is
        inversely proportional to number of class points.
        """
        # when testing, we load one whole scene every time
        # and we don't need label weight for loss calculation
        if not self.test_mode and scene_idxs is None:
            raise NotImplementedError(
                'please provide re-sampled scene indexes for training')

        return super().get_scene_idxs_and_label_weight(scene_idxs,
                                                       label_weight)
