"""
FiftyOne Zoo Datasets provided natively by the library.

| Copyright 2017-2021, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import logging
import os
import shutil

import eta.core.utils as etau
import eta.core.web as etaw

import fiftyone.types as fot
import fiftyone.utils.bdd as foub
import fiftyone.utils.coco as fouc
import fiftyone.utils.cityscapes as foucs
import fiftyone.utils.data as foud
import fiftyone.utils.hmdb51 as fouh
import fiftyone.utils.kitti as fouk
import fiftyone.utils.lfw as foul
import fiftyone.utils.openimages as fouo
import fiftyone.utils.ucf101 as fouu
import fiftyone.zoo.datasets as fozd


logger = logging.getLogger(__name__)


class FiftyOneDataset(fozd.ZooDataset):
    """Base class for zoo datasets that are provided natively by FiftyOne."""

    pass


class BDD100KDataset(FiftyOneDataset):
    """The Berkeley Deep Drive (BDD) dataset is one of the largest and most
    diverse video datasets for autonomous vehicles.

    The BDD100K dataset contains 100,000 video clips collected from more than
    50,000 rides covering New York, San Francisco Bay Area, and other regions.
    The dataset contains diverse scene types such as city streets, residential
    areas, and highways. Furthermore, the videos were recorded in diverse
    weather conditions at different times of the day.

    The videos are split into training (70K), validation (10K) and testing
    (20K) sets. Each video is 40 seconds long with 720p resolution and a frame
    rate of 30fps. The frame at the 10th second of each video is annotated for
    image classification, detection, and segmentation tasks.

    This version of the dataset contains only the 100K images extracted from
    the videos as described above, together with the image classification,
    detection, and segmentation labels.

    In order to load the BDD100K dataset, you must download the source data
    manually. The directory should be organized in the following format::

        source_dir/
            labels/
                bdd100k_labels_images_train.json
                bdd100k_labels_images_val.json
            images/
                100k/
                    train/
                    test/
                    val/

    You can register at https://bdd-data.berkeley.edu in order to get links to
    download the data.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        # The path to the source files that you manually downloaded
        source_dir = "/path/to/dir-with-bdd100k-files"

        dataset = foz.load_zoo_dataset(
            "bdd100k",
            split="validation",
            source_dir=source_dir,
        )

        session = fo.launch_app(dataset)

    Dataset size
        7.10 GB

    Source
        https://bdd-data.berkeley.edu

    Args:
        source_dir (None): the directory containing the manually downloaded
            BDD100K files
        copy_files (True): whether to move (False) or create copies (True) of
            the source files when populating the dataset directory
    """

    def __init__(self, source_dir=None, copy_files=True):
        self.source_dir = source_dir
        self.copy_files = copy_files

    @property
    def name(self):
        return "bdd100k"

    @property
    def tags(self):
        return ("image", "multilabel", "automotive", "manual")

    @property
    def supported_splits(self):
        return ("train", "validation", "test")

    @property
    def requires_manual_download(self):
        return True

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        #
        # BDD100K must be manually downloaded by the user in `source_dir`
        #
        # The download contains all splits, so we remove the split from
        # `dataset_dir` here and wrangle the whole dataset (if necessary)
        #
        dataset_dir = os.path.dirname(dataset_dir)  # remove split dir
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            foub.parse_bdd100k_dataset(
                self.source_dir, dataset_dir, copy_files=self.copy_files
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.BDDDataset()
        num_samples = foub.BDDDatasetImporter._get_num_samples(split_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, None


class Caltech101Dataset(FiftyOneDataset):
    """The Caltech-101 dataset of images.

    The dataset consists of pictures of objects belonging to 101 classes, plus
    one background clutter class (``BACKGROUND_Google``). Each image is
    labelled with a single object.

    Each class contains roughly 40 to 800 images, totalling around 9,000
    images. Images are of variable sizes, with typical edge lengths of 200-300
    pixels. This version contains image-level labels only.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("caltech101")

        session = fo.launch_app(dataset)

    Dataset size
        138.60 MB

    Source
        http://www.vision.caltech.edu/Image_Datasets/Caltech101
    """

    #
    # The source URL for the data is
    # http://www.vision.caltech.edu/Image_Datasets/Caltech101/101_ObjectCategories.tar.gz
    # but this now redirects to the Google Drive file below
    #
    _GDRIVE_ID = "137RyRjvTBkBiIfeYBNZBtViDHQ6_Ewsp"
    _ARCHIVE_NAME = "101_ObjectCategories.tar.gz"
    _DIR_IN_ARCHIVE = "101_ObjectCategories"

    @property
    def name(self):
        return "caltech101"

    @property
    def tags(self):
        return ("image", "classification")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        # Must always delete `scratch_dir` because it would be confused as a
        # class folder
        etau.delete_dir(scratch_dir)

        logger.info("Parsing dataset metadata")
        dataset_type = fot.ImageClassificationDirectoryTree()
        importer = foud.ImageClassificationDirectoryTreeImporter
        classes = importer._get_classes(dataset_dir)
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class Caltech256Dataset(FiftyOneDataset):
    """The Caltech-256 dataset of images.

    The dataset consists of pictures of objects belonging to 256 classes, plus
    one background clutter class (``clutter``). Each image is labelled with a
    single object.

    Each class contains between 80 and 827 images, totalling 30,607 images.
    Images are of variable sizes, with typical edge lengths of 80-800 pixels.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("caltech256")

        session = fo.launch_app(dataset)

    Dataset size
        1.16 GB

    Source
        http://www.vision.caltech.edu/Image_Datasets/Caltech256
    """

    #
    # The source URL for the data is
    # http://www.vision.caltech.edu/Image_Datasets/Caltech256/256_ObjectCategories.tar
    # but this now redirects to the Google Drive file below
    #
    _GDRIVE_ID = "1r6o0pSROcV1_VwT4oSjA2FBUSCWGuxLK"
    _ARCHIVE_NAME = "256_ObjectCategories.tar"
    _DIR_IN_ARCHIVE = "256_ObjectCategories"

    @property
    def name(self):
        return "caltech256"

    @property
    def tags(self):
        return ("image", "classification")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        # There are two extraneous items in the raw download...
        try:
            etau.delete_dir(os.path.join(dataset_dir, "056.dog", "greg"))
        except:
            pass

        try:
            etau.delete_file(
                os.path.join(dataset_dir, "198.spider", "RENAME2")
            )
        except:
            pass

        # Must always delete `scratch_dir` because it would be confused as a
        # class folder
        etau.delete_dir(scratch_dir)

        # Normalize labels
        logger.info("Normalizing labels")
        for old_label in etau.list_subdirs(dataset_dir):
            new_label = old_label.split(".", 1)[1]
            if new_label.endswith("-101"):
                new_label = new_label[:-4]

            etau.move_dir(
                os.path.join(dataset_dir, old_label),
                os.path.join(dataset_dir, new_label),
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.ImageClassificationDirectoryTree()
        importer = foud.ImageClassificationDirectoryTreeImporter
        classes = importer._get_classes(dataset_dir)
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class CityscapesDataset(FiftyOneDataset):
    """Cityscapes is a large-scale dataset that contains a diverse set of
    stereo video sequences recorded in street scenes from 50 different cities,
    with high quality pixel-level annotations of 5,000 frames in addition to a
    larger set of 20,000 weakly annotated frames.

    The dataset is intended for:

    -   Assessing the performance of vision algorithms for major tasks of
        semantic urban scene understanding: pixel-level, instance-level, and
        panoptic semantic labeling
    -   Supporting research that aims to exploit large volumes of (weakly)
        annotated data, e.g. for training deep neural networks

    In order to load the Cityscapes dataset, you must download the source data
    manually. The directory should be organized in the following format::

        source_dir/
            leftImg8bit_trainvaltest.zip
            gtFine_trainvaltest.zip             # optional
            gtCoarse.zip                        # optional
            gtBbox_cityPersons_trainval.zip     # optional

    You can register at https://www.cityscapes-dataset.com/register in order
    to get links to download the data.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        # The path to the source files that you manually downloaded
        source_dir = "/path/to/dir-with-cityscapes-files"

        dataset = foz.load_zoo_dataset(
            "cityscapes",
            split="validation",
            source_dir=source_dir,
        )

        session = fo.launch_app(dataset)

    Dataset size
        11.80 GB

    Source
        https://www.cityscapes-dataset.com

    Args:
        source_dir (None): a directory containing the manually downloaded
            Cityscapes files
        fine_annos (None): whether to load the fine annotations (True), or not
            (False), or only if the ZIP file exists (None)
        coarse_annos (None): whether to load the coarse annotations (True), or
            not (False), or only if the ZIP file exists (None)
        person_annos (None): whether to load the personn detections (True), or
            not (False), or only if the ZIP file exists (None)
    """

    def __init__(
        self,
        source_dir=None,
        fine_annos=None,
        coarse_annos=None,
        person_annos=None,
    ):
        self.source_dir = source_dir
        self.fine_annos = fine_annos
        self.coarse_annos = coarse_annos
        self.person_annos = person_annos

    @property
    def name(self):
        return "cityscapes"

    @property
    def tags(self):
        return ("image", "multilabel", "automotive", "manual")

    @property
    def supported_splits(self):
        return ("train", "validation", "test")

    @property
    def requires_manual_download(self):
        return True

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        #
        # Cityscapes is distributed as a single download that contains all
        # splits (which must be manually downloaded), so we remove the split
        # from `dataset_dir` and download the whole dataset (if necessary)
        #
        dataset_dir = os.path.dirname(dataset_dir)  # remove split dir
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            foucs.parse_cityscapes_dataset(
                self.source_dir,
                dataset_dir,
                scratch_dir,
                [split],
                fine_annos=self.fine_annos,
                coarse_annos=self.coarse_annos,
                person_annos=self.person_annos,
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.FiftyOneDataset()
        num_samples = foud.FiftyOneDatasetImporter._get_num_samples(split_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, None


class COCO2014Dataset(FiftyOneDataset):
    """COCO is a large-scale object detection, segmentation, and captioning
    dataset.

    This version contains images, bounding boxes, and segmentations for the
    2014 version of the dataset.

    This dataset supports partial downloads:

    -   You can specify subsets of data to download via the ``label_types``,
        ``classes``, and ``max_samples`` parameters
    -   You can specify specific images to load via the ``image_ids`` parameter

    See :ref:`this page <dataset-zoo-coco-2014>` for more information about
    partial downloads of this dataset.

    Full split stats:

    -   Train split: 82,783 images
    -   Test split: 40,775 images
    -   Validation split: 40,504 images

    Notes:

    -   COCO defines 91 classes but the data only uses 80 classes
    -   Some images from the train and validation sets don't have annotations
    -   The test set does not have annotations
    -   COCO 2014 and 2017 use the same images, but the splits are different

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        #
        # Load 50 random samples from the validation split
        #
        # By default, only detections are loaded
        #

        dataset = foz.load_zoo_dataset(
            "coco-2014",
            split="validation",
            max_samples=50,
            shuffle=True,
        )

        session = fo.launch_app(dataset)

        #
        # Load segmentations for 25 samples from the validation split that
        # contain cats and dogs
        #
        # Images that contain all `classes` will be prioritized first, followed
        # by images that contain at least one of the required `classes`. If
        # there are not enough images matching `classes` in the split to meet
        # `max_samples`, only the available images will be loaded.
        #
        # Images will only be downloaded if necessary
        #

        dataset = foz.load_zoo_dataset(
            "coco-2014",
            split="validation",
            label_types=["segmentations"],
            classes=["cat", "dog"],
            max_samples=25,
        )

        session.dataset = dataset

        #
        # Download the entire validation split and load both detections and
        # segmentations
        #
        # Subsequent partial loads of the validation split will never require
        # downloading any images
        #

        dataset = foz.load_zoo_dataset(
            "coco-2014",
            split="validation",
            label_types=["detections", "segmentations"],
        )

        session.dataset = dataset

    Dataset size
        37.57 GB

    Source
        http://cocodataset.org/#home

    Args:
        label_types (None): a label type or list of label types to load. The
            supported values are ``("detections", "segmentations")``. By
            default, only "detections" are loaded
        classes (None): a string or list of strings specifying required classes
            to load. If provided, only samples containing at least one instance
            of a specified class will be loaded
        image_ids (None): an optional list of specific image IDs to load. Can
            be provided in any of the following formats:

            -   a list of ``<image-id>`` ints or strings
            -   a list of ``<split>/<image-id>`` strings
            -   the path to a text (newline-separated), JSON, or CSV file
                containing the list of image IDs to load in either of the first
                two formats
        num_workers (None): the number of processes to use when downloading
            individual images. By default, ``multiprocessing.cpu_count()`` is
            used
        shuffle (False): whether to randomly shuffle the order in which samples
            are chosen for partial downloads
        seed (None): a random seed to use when shuffling
        max_samples (None): a maximum number of samples to load per split. If
            ``label_types`` and/or ``classes`` are also specified, first
            priority will be given to samples that contain all of the specified
            label types and/or classes, followed by samples that contain at
            least one of the specified labels types or classes. The actual
            number of samples loaded may be less than this maximum value if the
            dataset does not contain sufficient samples matching your
            requirements. By default, all matching samples are loaded
    """

    def __init__(
        self,
        label_types=None,
        classes=None,
        image_ids=None,
        num_workers=None,
        shuffle=None,
        seed=None,
        max_samples=None,
    ):
        self.label_types = label_types
        self.classes = classes
        self.image_ids = image_ids
        self.num_workers = num_workers
        self.shuffle = shuffle
        self.seed = seed
        self.max_samples = max_samples

    @property
    def name(self):
        return "coco-2014"

    @property
    def tags(self):
        return ("image", "detection", "segmentation")

    @property
    def supported_splits(self):
        return ("train", "validation", "test")

    @property
    def supports_partial_downloads(self):
        return True

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        num_samples, classes, downloaded = fouc.download_coco_dataset_split(
            dataset_dir,
            split,
            year="2014",
            label_types=self.label_types,
            classes=self.classes,
            image_ids=self.image_ids,
            num_workers=self.num_workers,
            shuffle=self.shuffle,
            seed=self.seed,
            max_samples=self.max_samples,
            raw_dir=self._get_raw_dir(dataset_dir),
            scratch_dir=scratch_dir,
        )

        dataset_type = fot.COCODetectionDataset()

        if not downloaded:
            num_samples = None

        return dataset_type, num_samples, classes

    def _get_raw_dir(self, dataset_dir):
        # A split-independent location to store full annotation files so that
        # they never need to be redownloaded
        root_dir = os.path.dirname(os.path.normpath(dataset_dir))
        return os.path.join(root_dir, "raw")


class COCO2017Dataset(FiftyOneDataset):
    """COCO is a large-scale object detection, segmentation, and captioning
    dataset.

    This version contains images, bounding boxes, segmentations, and keypoints
    for the 2017 version of the dataset.

    This dataset supports partial downloads:

    -   You can specify subsets of data to download via the ``label_types``,
        ``classes``, and ``max_samples`` parameters
    -   You can specify specific images to load via the ``image_ids`` parameter

    See :ref:`this page <dataset-zoo-coco-2017>` for more information about
    partial downloads of this dataset.

    Full split stats:

    -   Train split: 118,287 images
    -   Test split: 40,670 images
    -   Validation split: 5,000 images

    Notes:

    -   COCO defines 91 classes but the data only uses 80 classes
    -   Some images from the train and validation sets don't have annotations
    -   The test set does not have annotations
    -   COCO 2014 and 2017 use the same images, but the splits are different

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        #
        # Load 50 random samples from the validation split
        #
        # By default, only detections are loaded
        #

        dataset = foz.load_zoo_dataset(
            "coco-2017",
            split="validation",
            max_samples=50,
            shuffle=True,
        )

        session = fo.launch_app(dataset)

        #
        # Load segmentations for 25 samples from the validation split that
        # contain cats and dogs
        #
        # Images that contain all `classes` will be prioritized first, followed
        # by images that contain at least one of the required `classes`. If
        # there are not enough images matching `classes` in the split to meet
        # `max_samples`, only the available images will be loaded.
        #
        # Images will only be downloaded if necessary
        #

        dataset = foz.load_zoo_dataset(
            "coco-2017",
            split="validation",
            label_types=["segmentations"],
            classes=["cat", "dog"],
            max_samples=25,
        )

        session.dataset = dataset

        #
        # Download the entire validation split and load both detections and
        # segmentations
        #
        # Subsequent partial loads of the validation split will never require
        # downloading any images
        #

        dataset = foz.load_zoo_dataset(
            "coco-2017",
            split="validation",
            label_types=["detections", "segmentations"],
        )

        session.dataset = dataset

    Dataset size
        25.20 GB

    Source
        http://cocodataset.org/#home

    Args:
        label_types (None): a label type or list of label types to load. The
            supported values are ``("detections", "segmentations")``. By
            default, only "detections" are loaded
        classes (None): a string or list of strings specifying required classes
            to load. If provided, only samples containing at least one instance
            of a specified class will be loaded
        image_ids (None): an optional list of specific image IDs to load. Can
            be provided in any of the following formats:

            -   a list of ``<image-id>`` ints or strings
            -   a list of ``<split>/<image-id>`` strings
            -   the path to a text (newline-separated), JSON, or CSV file
                containing the list of image IDs to load in either of the first
                two formats
        num_workers (None): the number of processes to use when downloading
            individual images. By default, ``multiprocessing.cpu_count()`` is
            used
        shuffle (False): whether to randomly shuffle the order in which samples
            are chosen for partial downloads
        seed (None): a random seed to use when shuffling
        max_samples (None): a maximum number of samples to load per split. If
            ``label_types`` and/or ``classes`` are also specified, first
            priority will be given to samples that contain all of the specified
            label types and/or classes, followed by samples that contain at
            least one of the specified labels types or classes. The actual
            number of samples loaded may be less than this maximum value if the
            dataset does not contain sufficient samples matching your
            requirements. By default, all matching samples are loaded
    """

    def __init__(
        self,
        label_types=None,
        classes=None,
        image_ids=None,
        num_workers=None,
        shuffle=None,
        seed=None,
        max_samples=None,
    ):
        self.label_types = label_types
        self.classes = classes
        self.image_ids = image_ids
        self.num_workers = num_workers
        self.shuffle = shuffle
        self.seed = seed
        self.max_samples = max_samples

    @property
    def name(self):
        return "coco-2017"

    @property
    def tags(self):
        return ("image", "detection", "segmentation")

    @property
    def supported_splits(self):
        return ("train", "validation", "test")

    @property
    def supports_partial_downloads(self):
        return True

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        num_samples, classes, downloaded = fouc.download_coco_dataset_split(
            dataset_dir,
            split,
            year="2017",
            label_types=self.label_types,
            classes=self.classes,
            image_ids=self.image_ids,
            num_workers=self.num_workers,
            shuffle=self.shuffle,
            seed=self.seed,
            max_samples=self.max_samples,
            raw_dir=self._get_raw_dir(dataset_dir),
            scratch_dir=scratch_dir,
        )

        dataset_type = fot.COCODetectionDataset()

        if not downloaded:
            num_samples = None

        return dataset_type, num_samples, classes

    def _get_raw_dir(self, dataset_dir):
        # A split-independent location to store full annotation files so that
        # they never need to be redownloaded
        root_dir = os.path.dirname(os.path.normpath(dataset_dir))
        return os.path.join(root_dir, "raw")


class HMDB51Dataset(FiftyOneDataset):
    """HMDB51 is an action recognition dataset containing a total of 6,766
    clips distributed across 51 action classes.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("hmdb51", split="test")

        session = fo.launch_app(dataset)

    Dataset size
        2.16 GB

    Source
        https://serre-lab.clps.brown.edu/resource/hmdb-a-large-human-motion-database

    Args:
        fold (1): the test/train fold to use to arrange the files on disk. The
            supported values are ``(1, 2, 3)``
    """

    def __init__(self, fold=1):
        self.fold = fold

    @property
    def name(self):
        return "hmdb51"

    @property
    def tags(self):
        return ("video", "action-recognition")

    @property
    def parameters(self):
        return {"fold": self.fold}

    @property
    def supported_splits(self):
        return ("train", "test", "other")

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        #
        # HMDB51 is distributed as a single download that contains all splits,
        # so we remove the split from `dataset_dir` and download the whole
        # dataset (if necessary)
        #
        dataset_dir = os.path.dirname(dataset_dir)  # remove split dir
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            fouh.download_hmdb51_dataset(
                dataset_dir,
                scratch_dir=scratch_dir,
                fold=self.fold,
                cleanup=False,
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.VideoClassificationDirectoryTree()
        importer = foud.VideoClassificationDirectoryTreeImporter
        classes = importer._get_classes(split_dir)
        num_samples = importer._get_num_samples(split_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class ImageNetSampleDataset(FiftyOneDataset):
    """A small sample of images from the ImageNet 2012 dataset.

    The dataset contains 1,000 images, one randomly chosen from each class of
    the validation split of the ImageNet 2012 dataset.

    These images are provided according to the terms below:

    .. code-block:: text

        You have been granted access for non-commercial research/educational
        use. By accessing the data, you have agreed to the following terms.

        You (the "Researcher") have requested permission to use the ImageNet
        database (the "Database") at Princeton University and Stanford
        University. In exchange for such permission, Researcher hereby agrees
        to the following terms and conditions:

        1.  Researcher shall use the Database only for non-commercial research
            and educational purposes.
        2.  Princeton University and Stanford University make no
            representations or warranties regarding the Database, including but
            not limited to warranties of non-infringement or fitness for a
            particular purpose.
        3.  Researcher accepts full responsibility for his or her use of the
            Database and shall defend and indemnify Princeton University and
            Stanford University, including their employees, Trustees, officers
            and agents, against any and all claims arising from Researcher's
            use of the Database, including but not limited to Researcher's use
            of any copies of copyrighted images that he or she may create from
            the Database.
        4.  Researcher may provide research associates and colleagues with
            access to the Database provided that they first agree to be bound
            by these terms and conditions.
        5.  Princeton University and Stanford University reserve the right to
            terminate Researcher's access to the Database at any time.
        6.  If Researcher is employed by a for-profit, commercial entity,
            Researcher's employer shall also be bound by these terms and
            conditions, and Researcher hereby represents that he or she is
            fully authorized to enter into this agreement on behalf of such
            employer.
        7.  The law of the State of New Jersey shall apply to all disputes
            under this agreement.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("imagenet-sample")

        session = fo.launch_app(dataset)

    Dataset size
        98.26 MB

    Source
        http://image-net.org
    """

    _GDRIVE_ID = "1FZ9GpiRjiBbOS0iPyNZsS_B00W2RYSmS"
    _ARCHIVE_NAME = "imagenet-sample.zip"
    _DIR_IN_ARCHIVE = "imagenet-sample"

    @property
    def name(self):
        return "imagenet-sample"

    @property
    def tags(self):
        return ("image", "classification")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.FiftyOneImageClassificationDataset()
        importer = foud.FiftyOneImageClassificationDatasetImporter
        classes = importer._get_classes(dataset_dir)
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class KITTIDataset(FiftyOneDataset):
    """KITTI contains a suite of vision tasks built using an autonomous
    driving platform.

    The full benchmark contains many tasks such as stereo, optical flow, visual
    odometry, etc. This dataset contains the object detection dataset,
    including the monocular images and bounding boxes.

    The training split contains 7,481 images annotated with 2D and 3D bounding
    boxes (currently only the 2D detections are loaded), and the test split
    contains 7,518 unlabeled images.

    A full description of the annotations can be found in the README of the
    object development kit on the KITTI homepage.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("kitti", split="train")

        session = fo.launch_app(dataset)

    Dataset size
        11.71 GB

    Source
        http://www.cvlibs.net/datasets/kitti
    """

    @property
    def name(self):
        return "kitti"

    @property
    def tags(self):
        return ("image", "detection")

    @property
    def supported_splits(self):
        return ("train", "test")

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        split_dir = os.path.join(scratch_dir, split)
        if not os.path.isdir(split_dir):
            fouk.download_kitti_detection_dataset(
                scratch_dir, overwrite=False, cleanup=False
            )

        etau.move_dir(split_dir, dataset_dir)

        logger.info("Parsing dataset metadata")
        dataset_type = fot.KITTIDetectionDataset()
        importer = fouk.KITTIDetectionDatasetImporter
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, None


class LabeledFacesInTheWildDataset(FiftyOneDataset):
    """Labeled Faces in the Wild is a public benchmark for face verification,
    also known as pair matching.

    The dataset contains 13,233 images of 5,749 people's faces collected from
    the web. Each face has been labeled with the name of the person pictured.
    1,680 of the people pictured have two or more distinct photos in the data
    set. The only constraint on these faces is that they were detected by the
    Viola-Jones face detector.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("lfw", split="test")

        session = fo.launch_app(dataset)

    Dataset size
        173.00 MB

    Source
        http://vis-www.cs.umass.edu/lfw
    """

    @property
    def name(self):
        return "lfw"

    @property
    def tags(self):
        return ("image", "classification", "facial-recognition")

    @property
    def supported_splits(self):
        return ("train", "test")

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        #
        # LFW is distributed as a single download that contains all splits,
        # so we remove the split from `dataset_dir` and download the whole
        # dataset (if necessary)
        #
        dataset_dir = os.path.dirname(dataset_dir)  # remove split dir
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            foul.download_lfw_dataset(
                dataset_dir, scratch_dir=scratch_dir, cleanup=False
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.ImageClassificationDirectoryTree()
        importer = foud.ImageClassificationDirectoryTreeImporter
        classes = sorted(
            importer._get_classes(os.path.join(dataset_dir, "train"))
            + importer._get_classes(os.path.join(dataset_dir, "test"))
        )
        num_samples = importer._get_num_samples(split_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class OpenImagesV6Dataset(FiftyOneDataset):
    """Open Images V6 is a dataset of ~9 million images, roughly 2 million of
    which are annotated and available via this zoo dataset.

    The dataset contains annotations for classification, detection,
    segmentation, and visual relationship tasks for the 600 boxable object
    classes.

    This dataset supports partial downloads:

    -   You can specify subsets of data to download via the``label_types``,
        ``classes``, ``attrs``, and ``max_samples`` parameters
    -   You can specify specific images to load via the ``image_ids`` parameter

    See :ref:`this page <dataset-zoo-open-images-v6>` for more information
    about partial downloads of this dataset.

    Full split stats:

    -   Train split: 1,743,042 images (513 GB)
    -   Test split: 125,436 images (36 GB)
    -   Validation split: 41,620 images (12 GB)

    Notes:

    -   Not all images contain all types of labels
    -   All images have been rescaled so that their largest dimension is at
        most 1024 pixels

    Example usage::

        #
        # Load 50 random samples from the validation split
        #
        # By default, all label types are loaded
        #

        dataset = foz.load_zoo_dataset(
            "open-images-v6",
            split="validation",
            max_samples=50,
            shuffle=True,
        )

        session = fo.launch_app(dataset)

        #
        # Load detections and classifications for 25 samples from the
        # validation split that contain fedoras and pianos
        #
        # Images that contain all `label_types` and `classes` will be
        # prioritized first, followed by images that contain at least one of
        # the required `classes`. If there are not enough images matching
        # `classes` in the split to meet `max_samples`, only the available
        # images will be loaded.
        #
        # Images will only be downloaded if necessary
        #

        dataset = foz.load_zoo_dataset(
            "open-images-v6",
            split="validation",
            label_types=["detections", "classifications"],
            classes=["Fedora", "Piano"],
            max_samples=25,
        )

        session.dataset = dataset

        #
        # Download the entire validation split and load detections
        #
        # Subsequent partial loads of the validation split will never require
        # downloading any images
        #

        dataset = foz.load_zoo_dataset(
            "open-images-v6",
            split="validation",
            label_types=["detections"],
        )

        session.dataset = dataset

    Dataset size
        561 GB

    Source
        https://storage.googleapis.com/openimages/web/index.html

    Args:
        label_types (None): a label type or list of label types to load. The
            supported values are
            ``("detections", "classifications", "relationships", "segmentations")``.
            By default, all label types are loaded
        classes (None): a string or list of strings specifying required classes
            to load. If provided, only samples containing at least one instance
            of a specified class will be loaded
        attrs (None): a string or list of strings specifying required
            relationship attributes to load. Only applicable when
            ``label_types`` includes "relationships". If provided, only samples
            containing at least one instance of a specified attribute will be
            loaded
        image_ids (None): an optional list of specific image IDs to load. Can
            be provided in any of the following formats:

            -   a list of ``<image-id>`` strings
            -   a list of ``<split>/<image-id>`` strings
            -   the path to a text (newline-separated), JSON, or CSV file
                containing the list of image IDs to load in either of the first
                two formats
        num_workers (None): the number of processes to use when downloading
            individual images. By default, ``multiprocessing.cpu_count()`` is
            used
        shuffle (False): whether to randomly shuffle the order in which samples
            are chosen for partial downloads
        seed (None): a random seed to use when shuffling
        max_samples (None): a maximum number of samples to load per split. If
            ``label_types``, ``classes``, and/or ``attrs`` are also specified,
            first priority will be given to samples that contain all of the
            specified label types, classes, and/or attributes, followed by
            samples that contain at least one of the specified labels types or
            classes. The actual number of samples loaded may be less than this
            maximum value if the dataset does not contain sufficient samples
            matching your requirements. By default, all matching samples are
            loaded
    """

    def __init__(
        self,
        label_types=None,
        classes=None,
        attrs=None,
        image_ids=None,
        num_workers=None,
        shuffle=None,
        seed=None,
        max_samples=None,
    ):
        self.label_types = label_types
        self.classes = classes
        self.attrs = attrs
        self.image_ids = image_ids
        self.num_workers = num_workers
        self.shuffle = shuffle
        self.seed = seed
        self.max_samples = max_samples

    @property
    def name(self):
        return "open-images-v6"

    @property
    def tags(self):
        return (
            "image",
            "detection",
            "segmentation",
            "classification",
        )

    @property
    def supported_splits(self):
        return ("train", "test", "validation")

    @property
    def supports_partial_downloads(self):
        return True

    def _download_and_prepare(self, dataset_dir, _, split):
        num_samples, classes, downloaded = fouo.download_open_images_split(
            dataset_dir,
            split,
            version="v6",
            label_types=self.label_types,
            classes=self.classes,
            attrs=self.attrs,
            image_ids=self.image_ids,
            num_workers=self.num_workers,
            shuffle=self.shuffle,
            seed=self.seed,
            max_samples=self.max_samples,
        )

        dataset_type = fot.OpenImagesV6Dataset()

        if not downloaded:
            num_samples = None

        return dataset_type, num_samples, classes


class QuickstartDataset(FiftyOneDataset):
    """A small dataset with ground truth bounding boxes and predictions.

    The dataset consists of 200 images from the validation split of COCO-2017,
    with model predictions generated by an out-of-the-box Faster R-CNN model
    from
    `torchvision.models <https://pytorch.org/docs/stable/torchvision/models.html>`_.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("quickstart")

        session = fo.launch_app(dataset)

    Dataset size
        23.40 MB
    """

    _GDRIVE_ID = "1UWTlFmdq8H-wdJHxVsAKpXBilY1CWwm_"
    _ARCHIVE_NAME = "quickstart.zip"
    _DIR_IN_ARCHIVE = "quickstart"

    @property
    def name(self):
        return "quickstart"

    @property
    def tags(self):
        return ("image", "quickstart")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.FiftyOneDataset()
        importer = foud.FiftyOneDatasetImporter
        classes = importer._get_classes(dataset_dir)
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class QuickstartGeoDataset(FiftyOneDataset):
    """A small dataset with geolocation data.

    The dataset consists of 500 images from the validation split of the BDD100K
    dataset in the New York City area with object detections and GPS
    timestamps.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("quickstart-geo")

        session = fo.launch_app(dataset)

    Dataset size
        33.50 MB
    """

    _GDRIVE_ID = "1B2msoc3ej2RD0zVHoXNQmuJIjsPxLTfz"
    _ARCHIVE_NAME = "quickstart-geo.zip"
    _DIR_IN_ARCHIVE = "quickstart-geo"

    @property
    def name(self):
        return "quickstart-geo"

    @property
    def tags(self):
        return ("image", "location", "quickstart")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.FiftyOneDataset()
        importer = foud.FiftyOneDatasetImporter
        classes = importer._get_classes(dataset_dir)
        num_samples = importer._get_num_samples(dataset_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


class QuickstartVideoDataset(FiftyOneDataset):
    """A small video dataset with dense annotations.

    The dataset consists of 10 video segments with dense object detections
    generated by human annotators.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("quickstart-video")

        session = fo.launch_app(dataset)

    Dataset size
        35.20 MB
    """

    _GDRIVE_ID = "1O-WMjtiBBMXGEHnnus6y2nSlJu8pY5vo"
    _ARCHIVE_NAME = "quickstart-video.zip"
    _DIR_IN_ARCHIVE = "quickstart-video"

    @property
    def name(self):
        return "quickstart-video"

    @property
    def tags(self):
        return ("video", "quickstart")

    @property
    def supported_splits(self):
        return None

    def _download_and_prepare(self, dataset_dir, scratch_dir, _):
        _download_and_extract_archive(
            self._GDRIVE_ID,
            self._ARCHIVE_NAME,
            self._DIR_IN_ARCHIVE,
            dataset_dir,
            scratch_dir,
        )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.FiftyOneVideoLabelsDataset()
        num_samples = foud.FiftyOneVideoLabelsDatasetImporter._get_num_samples(
            dataset_dir
        )
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, None


class UCF101Dataset(FiftyOneDataset):
    """UCF101 is an action recognition data set of realistic action videos,
    collected from YouTube, having 101 action categories. This data set is an
    extension of UCF50 data set which has 50 action categories.

    With 13,320 videos from 101 action categories, UCF101 gives the largest
    diversity in terms of actions and with the presence of large variations in
    camera motion, object appearance and pose, object scale, viewpoint,
    cluttered background, illumination conditions, etc, it is the most
    challenging data set to date. As most of the available action recognition
    data sets are not realistic and are staged by actors, UCF101 aims to
    encourage further research into action recognition by learning and
    exploring new realistic action categories.

    The videos in 101 action categories are grouped into 25 groups, where each
    group can consist of 4-7 videos of an action. The videos from the same
    group may share some common features, such as similar background, similar
    viewpoint, etc.

    Example usage::

        import fiftyone as fo
        import fiftyone.zoo as foz

        dataset = foz.load_zoo_dataset("ucf101", split="test")

        session = fo.launch_app(dataset)

    Dataset size
        6.48 GB

    Source
        https://www.crcv.ucf.edu/research/data-sets/ucf101

    Args:
        fold (1): the test/train fold to use to arrange the files on disk. The
            supported values are ``(1, 2, 3)``
    """

    def __init__(self, fold=1):
        self.fold = fold

    @property
    def name(self):
        return "ucf101"

    @property
    def tags(self):
        return ("video", "action-recognition")

    @property
    def parameters(self):
        return {"fold": self.fold}

    @property
    def supported_splits(self):
        return ("train", "test")

    def _download_and_prepare(self, dataset_dir, scratch_dir, split):
        #
        # UCF101 is distributed as a single download that contains all splits,
        # so we remove the split from `dataset_dir` and download the whole
        # dataset (if necessary)
        #
        dataset_dir = os.path.dirname(dataset_dir)  # remove split dir
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            fouu.download_ucf101_dataset(
                dataset_dir,
                scratch_dir=scratch_dir,
                fold=self.fold,
                cleanup=False,
            )

        logger.info("Parsing dataset metadata")
        dataset_type = fot.VideoClassificationDirectoryTree()
        importer = foud.VideoClassificationDirectoryTreeImporter
        classes = importer._get_classes(split_dir)
        num_samples = importer._get_num_samples(split_dir)
        logger.info("Found %d samples", num_samples)

        return dataset_type, num_samples, classes


AVAILABLE_DATASETS = {
    "bdd100k": BDD100KDataset,
    "caltech101": Caltech101Dataset,
    "caltech256": Caltech256Dataset,
    "cityscapes": CityscapesDataset,
    "coco-2014": COCO2014Dataset,
    "coco-2017": COCO2017Dataset,
    "hmdb51": HMDB51Dataset,
    "imagenet-sample": ImageNetSampleDataset,
    "kitti": KITTIDataset,
    "lfw": LabeledFacesInTheWildDataset,
    "open-images-v6": OpenImagesV6Dataset,
    "quickstart": QuickstartDataset,
    "quickstart-geo": QuickstartGeoDataset,
    "quickstart-video": QuickstartVideoDataset,
    "ucf101": UCF101Dataset,
}


def _download_and_extract_archive(
    fid, archive_name, dir_in_archive, dataset_dir, scratch_dir
):
    archive_path = os.path.join(scratch_dir, archive_name)
    if not os.path.exists(archive_path):
        logger.info("Downloading dataset...")
        etaw.download_google_drive_file(fid, path=archive_path)
    else:
        logger.info("Using existing archive '%s'", archive_path)

    logger.info("Extracting dataset...")
    etau.extract_archive(archive_path)
    _move_dir(os.path.join(scratch_dir, dir_in_archive), dataset_dir)


def _move_dir(src, dst):
    for f in os.listdir(src):
        shutil.move(os.path.join(src, f), dst)
