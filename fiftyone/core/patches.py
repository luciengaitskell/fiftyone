"""
Patches views.

| Copyright 2017-2021, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from copy import deepcopy

import eta.core.utils as etau

import fiftyone.core.aggregations as foa
import fiftyone.core.dataset as fod
import fiftyone.core.fields as fof
import fiftyone.core.labels as fol
import fiftyone.core.media as fom
import fiftyone.core.sample as fos
import fiftyone.core.view as fov


_SINGLE_TYPES_MAP = {
    fol.Detections: fol.Detection,
    fol.Polylines: fol.Polyline,
}
_PATCHES_TYPES = (fol.Detections, fol.Polylines)
_NO_MATCH_ID = ""


class _PatchView(fos.SampleView):
    @property
    def _sample_id(self):
        return self._doc.sample_id

    @property
    def _frame_id(self):
        return self._doc.frame_id

    def save(self):
        super().save()
        self._view._sync_source_sample(self)


class PatchView(_PatchView):
    """A patch in a :class:`PatchesView`.

    :class:`PatchView` instances should not be created manually; they are
    generated by iterating over :class:`PatchesView` instances.

    Args:
        doc: a :class:`fiftyone.core.odm.DatasetSampleDocument`
        view: the :class:`PatchesView` that the patch belongs to
        selected_fields (None): a set of field names that this view is
            restricted to
        excluded_fields (None): a set of field names that are excluded from
            this view
        filtered_fields (None): a set of field names of list fields that are
            filtered in this view
    """

    pass


class EvaluationPatchView(_PatchView):
    """A patch in an :class:`EvaluationPatchesView`.

    :class:`EvaluationPatchView` instances should not be created manually; they
    are generated by iterating over :class:`EvaluationPatchesView` instances.

    Args:
        doc: a :class:`fiftyone.core.odm.DatasetSampleDocument`
        view: the :class:`EvaluationPatchesView` that the patch belongs to
        selected_fields (None): a set of field names that this view is
            restricted to
        excluded_fields (None): a set of field names that are excluded from
            this view
        filtered_fields (None): a set of field names of list fields that are
            filtered in this view
    """

    pass


class _PatchesView(fov.DatasetView):
    def __init__(
        self, source_collection, patches_stage, patches_dataset, _stages=None
    ):
        if _stages is None:
            _stages = []

        self._source_collection = source_collection
        self._patches_stage = patches_stage
        self._patches_dataset = patches_dataset
        self.__stages = _stages

    def __copy__(self):
        return self.__class__(
            self._source_collection,
            deepcopy(self._patches_stage),
            self._patches_dataset,
            _stages=deepcopy(self.__stages),
        )

    @property
    def _base_view(self):
        return self.__class__(
            self._source_collection,
            self._patches_stage,
            self._patches_dataset,
        )

    @property
    def _dataset(self):
        return self._patches_dataset

    @property
    def _root_dataset(self):
        return self._source_collection._root_dataset

    @property
    def _is_frames(self):
        return self._source_collection._is_frames

    @property
    def _stages(self):
        return self.__stages

    @property
    def _all_stages(self):
        return (
            self._source_collection.view()._all_stages
            + [self._patches_stage]
            + self.__stages
        )

    @property
    def _id_field(self):
        if self._is_frames:
            return "frame_id"

        return "sample_id"

    @property
    def _label_fields(self):
        raise NotImplementedError("subclass must implement _label_fields")

    @property
    def _element_str(self):
        return "patch"

    @property
    def _elements_str(self):
        return "patches"

    @property
    def name(self):
        return self.dataset_name + "-patches"

    def _get_default_sample_fields(
        self, include_private=False, use_db_fields=False
    ):
        fields = super()._get_default_sample_fields(
            include_private=include_private, use_db_fields=use_db_fields
        )

        extras = ["_sample_id" if use_db_fields else "sample_id"]

        if self._is_frames:
            extras.append("_frame_id" if use_db_fields else "frame_id")
            extras.append("frame_number")

        return fields + tuple(extras)

    def _get_default_indexes(self, frames=False):
        if frames:
            return super()._get_default_indexes(frames=frames)

        names = ["id", "filepath", "sample_id"]
        if self._is_frames:
            names.extend(["frame_id", "_sample_id_1_frame_number_1"])

        return names

    def set_values(self, field_name, *args, **kwargs):
        field = field_name.split(".", 1)[0]
        must_sync = field in self._label_fields

        # The `set_values()` operation could change the contents of this view,
        # so we first record the sample IDs that need to be synced
        if must_sync and self._stages:
            ids = self.values("_id")
        else:
            ids = None

        super().set_values(field_name, *args, **kwargs)

        if must_sync:
            self._sync_source_field(field, ids=ids)

    def save(self, fields=None):
        """Overwrites the object patches in the source dataset with the
        contents of this view.

        If this view contains any additional fields that were not extracted
        from the source dataset, these fields are not saved.

        .. warning::

            This will permanently delete any omitted or filtered contents from
            the source dataset.

        Args:
            fields (None): an optional field or list of fields to save. If
                specified, only these fields are overwritten
        """
        if etau.is_str(fields):
            fields = [fields]

        super().save(fields=fields)

        if fields is None:
            fields = self._label_fields
        else:
            fields = [l for l in fields if l in self._label_fields]

        #
        # IMPORTANT: we sync the contents of `_patches_dataset`, not `self`
        # here because the `save()` call above updated the dataset, which means
        # this view may no longer have the same contents (e.g., if `skip()` is
        # involved)
        #

        self._sync_source_root(fields)

    def reload(self):
        """Reloads this view from the source collection in the database.

        Note that :class:`PatchView` instances are not singletons, so any
        in-memory patches extracted from this view will not be updated by
        calling this method.
        """
        self._source_collection.reload()

        #
        # Regenerate the patches dataset
        #
        # This assumes that calling `load_view()` when the current patches
        # dataset has been deleted will cause a new one to be generated
        #

        self._patches_dataset.delete()
        _view = self._patches_stage.load_view(self._source_collection)
        self._patches_dataset = _view._patches_dataset

    def _sync_source_sample(self, sample):
        for field in self._label_fields:
            self._sync_source_sample_field(sample, field)

    def _sync_source_sample_field(self, sample, field):
        label_type = self._patches_dataset._get_label_field_type(field)
        is_list_field = issubclass(label_type, fol._LABEL_LIST_FIELDS)

        sample_id = sample[self._id_field]

        doc = sample._doc.field_to_mongo(field)
        if is_list_field:
            doc = doc[label_type._LABEL_LIST_FIELD]

        self._source_collection._set_labels(field, [sample_id], [doc])

    def _sync_source_field(self, field, ids=None):
        _, label_path = self._patches_dataset._get_label_field_path(field)

        if ids is not None:
            view = self._patches_dataset.mongo(
                [{"$match": {"_id": {"$in": ids}}}]
            )
        else:
            view = self._patches_dataset

        sample_ids, docs = view.aggregate(
            [foa.Values(self._id_field), foa.Values(label_path, _raw=True)]
        )

        self._source_collection._set_labels(field, sample_ids, docs)

    def _sync_source_root(self, fields):
        for field in fields:
            self._sync_source_root_field(field)

    def _sync_source_root_field(self, field):
        _, label_id_path = self._get_label_field_path(field, "id")
        label_path = label_id_path.rsplit(".", 1)[0]

        #
        # Sync label updates
        #

        sample_ids, docs, label_ids = self._patches_dataset.aggregate(
            [
                foa.Values(self._id_field),
                foa.Values(label_path, _raw=True),
                foa.Values(label_id_path, unwind=True),
            ]
        )

        self._source_collection._set_labels(field, sample_ids, docs)

        #
        # Sync label deletions
        #

        _, src_id_path = self._source_collection._get_label_field_path(
            field, "id"
        )
        src_ids = self._source_collection.values(src_id_path, unwind=True)
        delete_ids = set(src_ids) - set(label_ids)

        if delete_ids:
            self._source_collection._delete_labels(
                ids=delete_ids, fields=field
            )


class PatchesView(_PatchesView):
    """A :class:`fiftyone.core.view.DatasetView` of patches from a
    :class:`fiftyone.core.dataset.Dataset`.

    Patches views contain an ordered collection of patch samples, each of which
    contains a subset of a sample of the parent dataset corresponding to a
    single object or logical grouping of of objects.

    Patches retrieved from patches views are returned as :class:`PatchView`
    objects.

    Args:
        source_collection: the
            :class:`fiftyone.core.collections.SampleCollection` from which this
            view was created
        patches_stage: the :class:`fiftyone.core.stages.ToPatches` stage that
            defines how the patches were extracted
        patches_dataset: the :class:`fiftyone.core.dataset.Dataset` that serves
            the patches in this view
    """

    def __init__(
        self, source_collection, patches_stage, patches_dataset, _stages=None
    ):
        super().__init__(
            source_collection, patches_stage, patches_dataset, _stages=_stages
        )

        self._patches_field = patches_stage.field

    @property
    def _sample_cls(self):
        return PatchView

    @property
    def _label_fields(self):
        return [self._patches_field]

    @property
    def patches_field(self):
        """The field from which the patches in this view were extracted."""
        return self._patches_field


class EvaluationPatchesView(_PatchesView):
    """A :class:`fiftyone.core.view.DatasetView` containing evaluation patches
    from a :class:`fiftyone.core.dataset.Dataset`.

    Evalation patches views contain an ordered collection of evaluation
    examples, each of which contains the ground truth and/or predicted labels
    for a true positive, false positive, or false negative example from an
    evaluation run on the underlying dataset.

    Patches retrieved from patches views are returned as
    :class:`EvaluationPatchView` objects.

    Args:
        source_collection: the
            :class:`fiftyone.core.collections.SampleCollection` from which this
            view was created
        patches_stage: the :class:`fiftyone.core.stages.ToEvaluationPatches`
            stage that defines how the patches were extracted
        patches_dataset: the :class:`fiftyone.core.dataset.Dataset` that serves
            the patches in this view
    """

    def __init__(
        self, source_collection, patches_stage, patches_dataset, _stages=None
    ):
        super().__init__(
            source_collection, patches_stage, patches_dataset, _stages=_stages
        )

        eval_key = patches_stage.eval_key
        eval_info = source_collection.get_evaluation_info(eval_key)
        self._gt_field = eval_info.config.gt_field
        self._pred_field = eval_info.config.pred_field

    @property
    def _sample_cls(self):
        return EvaluationPatchView

    @property
    def _label_fields(self):
        return [self._gt_field, self._pred_field]

    @property
    def gt_field(self):
        """The ground truth field for the evaluation patches in this view."""
        return self._gt_field

    @property
    def pred_field(self):
        """The predictions field for the evaluation patches in this view."""
        return self._pred_field


def make_patches_dataset(
    sample_collection, field, other_fields=None, keep_label_lists=False
):
    """Creates a dataset that contains one sample per object patch in the
    specified field of the collection.

    A ``sample_id`` field will be added that records the sample ID from which
    each patch was taken.

    By default, fields other than ``field`` and the default sample fields will
    not be included in the returned dataset.

    Args:
        sample_collection: a
            :class:`fiftyone.core.collections.SampleCollection`
        field: the patches field, which must be of type
            :class:`fiftyone.core.labels.Detections` or
            :class:`fiftyone.core.labels.Polylines`
        other_fields (None): controls whether fields other than ``field`` and
            the default sample fields are included. Can be any of the
            following:

            -   a field or list of fields to include
            -   ``True`` to include all other fields
            -   ``None``/``False`` to include no other fields
        keep_label_lists (False): whether to store the patches in label list
            fields of the same type as the input collection rather than using
            their single label variants

    Returns:
        a :class:`fiftyone.core.dataset.Dataset`
    """
    if sample_collection._is_frame_field(field):
        raise ValueError(
            "Frame label patches cannot be directly extracted; you must first "
            "convert your video dataset to frames via `to_frames()`"
        )

    if etau.is_str(other_fields):
        other_fields = [other_fields]

    is_frame_patches = sample_collection._is_frames

    if keep_label_lists:
        field_type = sample_collection._get_label_field_type(field)
    else:
        field_type = _get_single_label_field_type(sample_collection, field)

    dataset = fod.Dataset(_patches=True)
    dataset.media_type = fom.IMAGE
    dataset.add_sample_field(
        "sample_id", fof.ObjectIdField, db_field="_sample_id"
    )
    dataset.create_index("sample_id")

    if is_frame_patches:
        dataset.add_sample_field(
            "frame_id", fof.ObjectIdField, db_field="_frame_id"
        )
        dataset.add_sample_field("frame_number", fof.FrameNumberField)
        dataset.create_index("frame_id")
        dataset.create_index([("sample_id", 1), ("frame_number", 1)])

    dataset.add_sample_field(
        field, fof.EmbeddedDocumentField, embedded_doc_type=field_type
    )

    if other_fields:
        src_schema = sample_collection.get_field_schema()
        curr_schema = dataset.get_field_schema()

        if other_fields == True:
            other_fields = [f for f in src_schema if f not in curr_schema]

        add_fields = [f for f in other_fields if f not in curr_schema]
        dataset._sample_doc_cls.merge_field_schema(
            {k: v for k, v in src_schema.items() if k in add_fields}
        )

    _make_pretty_summary(dataset, is_frame_patches=is_frame_patches)

    patches_view = _make_patches_view(
        sample_collection,
        field,
        other_fields=other_fields,
        keep_label_lists=keep_label_lists,
    )
    _write_samples(dataset, patches_view)

    return dataset


def _get_single_label_field_type(sample_collection, field):
    label_type = sample_collection._get_label_field_type(field)

    if label_type not in _SINGLE_TYPES_MAP:
        raise ValueError("Unsupported label field type %s" % label_type)

    return _SINGLE_TYPES_MAP[label_type]


def make_evaluation_patches_dataset(
    sample_collection, eval_key, other_fields=None
):
    """Creates a dataset based on the results of the evaluation with the given
    key that contains one sample for each true positive, false positive, and
    false negative example in the input collection, respectively.

    True positive examples will result in samples with both their ground truth
    and predicted fields populated, while false positive/negative examples will
    only have one of their corresponding predicted/ground truth fields
    populated, respectively.

    If multiple predictions are matched to a ground truth object (e.g., if the
    evaluation protocol includes a crowd attribute), then all matched
    predictions will be stored in the single sample along with the ground truth
    object.

    The returned dataset will also have top-level ``type`` and ``iou`` fields
    populated based on the evaluation results for that example, as well as a
    ``sample_id`` field recording the sample ID of the example, and a ``crowd``
    field if the evaluation protocol defines a crowd attribute.

    .. note::

        The returned dataset will contain patches for the contents of the input
        collection, which may differ from the view on which the ``eval_key``
        evaluation was performed. This may exclude some labels that were
        evaluated and/or include labels that were not evaluated.

        If you would like to see patches for the exact view on which an
        evaluation was performed, first call
        :meth:`load_evaluation_view() <fiftyone.core.collections.SampleCollection.load_evaluation_view>`
        to load the view and then convert to patches.

    Args:
        sample_collection: a
            :class:`fiftyone.core.collections.SampleCollection`
        eval_key: an evaluation key that corresponds to the evaluation of
            ground truth/predicted fields that are of type
            :class:`fiftyone.core.labels.Detections` or
            :class:`fiftyone.core.labels.Polylines`
        other_fields (None): controls whether fields other than the
            ground truth/predicted fields and the default sample fields are
            included. Can be any of the following:

            -   a field or list of fields to include
            -   ``True`` to include all other fields
            -   ``None``/``False`` to include no other fields

    Returns:
        a :class:`fiftyone.core.dataset.Dataset`
    """
    # Parse evaluation info
    eval_info = sample_collection.get_evaluation_info(eval_key)
    pred_field = eval_info.config.pred_field
    gt_field = eval_info.config.gt_field
    if hasattr(eval_info.config, "iscrowd"):
        crowd_attr = eval_info.config.iscrowd
    else:
        crowd_attr = None

    is_frame_patches = sample_collection._is_frames

    if is_frame_patches:
        if not pred_field.startswith(sample_collection._FRAMES_PREFIX):
            raise ValueError(
                "Cannot extract evaluation patches for sample-level "
                "evaluation '%s' from a frames view" % eval_key
            )

        pred_field = pred_field[len(sample_collection._FRAMES_PREFIX) :]
        gt_field = gt_field[len(sample_collection._FRAMES_PREFIX) :]
    elif sample_collection._is_frame_field(pred_field):
        raise ValueError(
            "Frame evaluation patches cannot be directly extracted; you must "
            "first convert your video dataset to frames via `to_frames()`"
        )

    if etau.is_str(other_fields):
        other_fields = [other_fields]

    pred_type = sample_collection._get_label_field_type(pred_field)
    gt_type = sample_collection._get_label_field_type(gt_field)

    # Setup dataset with correct schema
    dataset = fod.Dataset(_patches=True)
    dataset.media_type = fom.IMAGE
    dataset.add_sample_field(
        "sample_id", fof.ObjectIdField, db_field="_sample_id"
    )
    dataset.create_index("sample_id")

    if is_frame_patches:
        dataset.add_sample_field(
            "frame_id", fof.ObjectIdField, db_field="_frame_id"
        )
        dataset.add_sample_field("frame_number", fof.FrameNumberField)
        dataset.create_index("frame_id")
        dataset.create_index([("sample_id", 1), ("frame_number", 1)])

    dataset.add_sample_field(
        gt_field, fof.EmbeddedDocumentField, embedded_doc_type=gt_type
    )
    dataset.add_sample_field(
        pred_field, fof.EmbeddedDocumentField, embedded_doc_type=pred_type
    )

    if crowd_attr is not None:
        dataset.add_sample_field("crowd", fof.BooleanField)

    dataset.add_sample_field("type", fof.StringField)
    dataset.add_sample_field("iou", fof.FloatField)

    if other_fields:
        src_schema = sample_collection.get_field_schema()
        curr_schema = dataset.get_field_schema()

        if other_fields == True:
            other_fields = [f for f in src_schema if f not in curr_schema]

        add_fields = [f for f in other_fields if f not in curr_schema]
        dataset._sample_doc_cls.merge_field_schema(
            {k: v for k, v in src_schema.items() if k in add_fields}
        )

    _make_pretty_summary(dataset, is_frame_patches=is_frame_patches)

    # Add ground truth patches
    gt_view = _make_eval_view(
        sample_collection,
        eval_key,
        gt_field,
        other_fields=other_fields,
        crowd_attr=crowd_attr,
    )
    _write_samples(dataset, gt_view)

    # Merge matched predictions
    _merge_matched_labels(dataset, sample_collection, eval_key, pred_field)

    # Add unmatched predictions
    unmatched_pred_view = _make_eval_view(
        sample_collection,
        eval_key,
        pred_field,
        other_fields=other_fields,
        skip_matched=True,
    )
    _add_samples(dataset, unmatched_pred_view)

    return dataset


def _make_pretty_summary(dataset, is_frame_patches=False):
    if is_frame_patches:
        set_fields = [
            "id",
            "sample_id",
            "frame_id",
            "filepath",
            "frame_number",
        ]
    else:
        set_fields = ["id", "sample_id", "filepath"]

    all_fields = dataset._sample_doc_cls._fields_ordered
    pretty_fields = set_fields + [f for f in all_fields if f not in set_fields]
    dataset._sample_doc_cls._fields_ordered = tuple(pretty_fields)


def _make_patches_view(
    sample_collection, field, other_fields=None, keep_label_lists=False
):
    label_type = sample_collection._get_label_field_type(field)
    if issubclass(label_type, _PATCHES_TYPES):
        list_field = field + "." + label_type._LABEL_LIST_FIELD
    else:
        raise ValueError(
            "Invalid label field type %s. Extracting patches is only "
            "supported for the following types: %s"
            % (label_type, _PATCHES_TYPES)
        )

    project = {
        "_id": False,
        "_media_type": True,
        "filepath": True,
        "metadata": True,
        "tags": True,
        field + "._cls": True,
        list_field: True,
    }

    if other_fields is not None:
        project.update({f: True for f in other_fields})

    if sample_collection._is_frames:
        project["_sample_id"] = True
        project["_frame_id"] = "$_id"
        project["frame_number"] = True
    else:
        project["_sample_id"] = "$_id"

    pipeline = [
        {"$project": project},
        {"$unwind": "$" + list_field},
        {"$set": {"_rand": {"$rand": {}}}},
        {"$set": {"_id": "$" + list_field + "._id"}},
    ]

    if keep_label_lists:
        pipeline.append({"$set": {list_field: ["$" + list_field]}})
    else:
        pipeline.append({"$set": {field: "$" + list_field}})

    return sample_collection.mongo(pipeline)


def _make_eval_view(
    sample_collection,
    eval_key,
    field,
    other_fields=None,
    skip_matched=False,
    crowd_attr=None,
):
    eval_type = field + "." + eval_key
    eval_id = field + "." + eval_key + "_id"
    eval_iou = field + "." + eval_key + "_iou"

    view = _make_patches_view(
        sample_collection, field, other_fields=other_fields
    )

    if skip_matched:
        view = view.mongo(
            [
                {
                    "$match": {
                        "$expr": {
                            "$or": [
                                {"$eq": ["$" + eval_id, _NO_MATCH_ID]},
                                {"$not": {"$gt": ["$" + eval_id, None]}},
                            ]
                        }
                    }
                }
            ]
        )

    view = view.mongo(
        [{"$set": {"type": "$" + eval_type, "iou": "$" + eval_iou}}]
    )

    if crowd_attr is not None:
        crowd_path1 = "$" + field + "." + crowd_attr

        # @todo can remove this when `Attributes` are deprecated
        crowd_path2 = "$" + field + ".attributes." + crowd_attr + ".value"

        view = view.mongo(
            [
                {
                    "$set": {
                        "crowd": {
                            "$cond": {
                                "if": {"$gt": [crowd_path1, None]},
                                "then": {"$toBool": crowd_path1},
                                "else": {
                                    "$cond": {
                                        "if": {"$gt": [crowd_path2, None]},
                                        "then": {"$toBool": crowd_path2},
                                        "else": None,
                                    }
                                },
                            }
                        }
                    }
                }
            ]
        )

    return _upgrade_labels(view, field)


def _upgrade_labels(view, field):
    tmp_field = "_" + field
    label_type = view._get_label_field_type(field)
    return view.mongo(
        [
            {"$set": {tmp_field: "$" + field}},
            {"$unset": field},
            {
                "$set": {
                    field: {
                        "_cls": label_type.__name__,
                        label_type._LABEL_LIST_FIELD: ["$" + tmp_field],
                    }
                }
            },
            {"$unset": tmp_field},
        ]
    )


def _merge_matched_labels(dataset, src_collection, eval_key, field):
    field_type = src_collection._get_label_field_type(field)

    list_field = field + "." + field_type._LABEL_LIST_FIELD
    eval_id = eval_key + "_id"
    eval_field = list_field + "." + eval_id

    pipeline = src_collection._pipeline()
    pipeline.extend(
        [
            {"$project": {list_field: True}},
            {"$unwind": "$" + list_field},
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$gt": ["$" + eval_field, None]},
                            {"$ne": ["$" + eval_field, _NO_MATCH_ID]},
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {"$toObjectId": "$" + eval_field},
                    "_labels": {"$push": "$" + list_field},
                }
            },
            {
                "$project": {
                    field: {
                        "_cls": field_type.__name__,
                        field_type._LABEL_LIST_FIELD: "$_labels",
                    }
                },
            },
            {
                "$merge": {
                    "into": dataset._sample_collection_name,
                    "on": "_id",
                    "whenMatched": "merge",
                    "whenNotMatched": "discard",
                }
            },
        ]
    )

    src_collection._dataset._aggregate(pipeline=pipeline)


def _write_samples(dataset, src_collection):
    pipeline = src_collection._pipeline(detach_frames=True)
    pipeline.append({"$out": dataset._sample_collection_name})

    src_collection._dataset._aggregate(pipeline=pipeline)


def _add_samples(dataset, src_collection):
    pipeline = src_collection._pipeline(detach_frames=True)
    pipeline.append(
        {
            "$merge": {
                "into": dataset._sample_collection_name,
                "on": "_id",
                "whenMatched": "keepExisting",
                "whenNotMatched": "insert",
            }
        }
    )

    src_collection._dataset._aggregate(pipeline=pipeline)
