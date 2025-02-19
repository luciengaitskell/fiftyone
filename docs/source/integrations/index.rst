.. _integrations:

FiftyOne Integrations
=====================

.. default-role:: code

FiftyOne integrates naturally with other ML tools that you know and love. Click
on the cards below to see how!

.. Integrations cards section -----------------------------------------------------

.. raw:: html

    <div id="tutorial-cards-container">

    <nav class="navbar navbar-expand-lg navbar-light tutorials-nav col-12">
        <div class="tutorial-tags-container">
            <div id="dropdown-filter-tags">
                <div class="tutorial-filter-menu">
                    <div class="tutorial-filter filter-btn all-tag-selected" data-tag="all">All</div>
                </div>
            </div>
        </div>
    </nav>

    <hr class="tutorials-hr">

    <div class="row">

    <div id="tutorial-cards">
    <div class="list">

.. Add tutorial cards below

.. customcarditem::
    :header: Lightning Flash
    :description: Train Flash models on FiftyOne datasets and use the FiftyOne App to visualize and improve your Flash models, all with just a few lines of code.
    :link: lightning_flash.html
    :image: ../_static/images/integrations/lightning_flash.png
    :tags: Model-Training,Model-Evaluation

.. customcarditem::
    :header: Open Images Dataset
    :description: See why FiftyOne is a recommended tool for downloading, visualizing, and evaluating on Google's Open Images Dataset.
    :link: open_images.html
    :image: ../_static/images/integrations/open_images.png
    :tags: Datasets,Model-Evaluation

.. customcarditem::
    :header: COCO Dataset
    :description: See how FiftyOne makes downloading, visualizing, and evaluating on the COCO dataset (or your own COCO-formatted data) a breeze.
    :link: coco.html
    :image: ../_static/images/integrations/coco.png
    :tags: Datasets,Model-Evaluation

.. customcarditem::
    :header: CVAT
    :description: Use our CVAT integration to easily annotate and edit your FiftyOne datasets.
    :link: cvat.html
    :image: ../_static/images/integrations/cvat.png
    :tags: Annotation

.. Upcoming integrations :)

    .. customcarditem::
        :header: Labelbox
        :description: Use our Labelbox integration to easily annotate and edit your FiftyOne datasets.
        :link: ../api/fiftyone.utils.labelbox.html
        :image: https://voxel51.com/images/integrations/labelbox-128.png
        :tags: Annotation

    .. customcarditem::
        :header: Scale AI
        :description: Use our Scale integration to easily annotate and edit your FiftyOne datasets.
        :link: ../api/fiftyone.utils.scale.html
        :image: https://voxel51.com/images/integrations/scale-128.png
        :tags: Annotation

.. End of integrations cards

.. raw:: html

    </div>

    <div class="pagination d-flex justify-content-center"></div>

    </div>

    </div>

.. End integrations cards section -------------------------------------------------

.. toctree::
   :maxdepth: 1
   :hidden:

    Lightning Flash <lightning_flash.rst>
    Open Images <open_images.rst>
    COCO <coco.rst>
    CVAT <cvat.rst>
