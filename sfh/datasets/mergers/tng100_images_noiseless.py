
"""tng100_images_noiseless dataset."""
import matplotlib.pyplot as plt
import numpy as np
from numpy import random
from numpy import loadtxt
import pandas as pd
import os
from astropy.utils.data import get_pkg_data_filename
from astropy.io import fits
from astropy.visualization import simple_norm
import tensorflow as tf
import tensorflow_datasets as tfds


## My functions added ##
def stack_bands(img_dir,gal_id):
  """
  For a given image path and galaxy id, stacks the four bands g,r,i,z into a single image
  Input: img_dir (str): path to the directory containing the noisy images
         gal_id (int): number of the image of galaxy for which you want to stack bands
  Output: im (numpy ndarray): resulting image with the four stacked bands
  """
  filters=['g','r','i','z']
  filenames=[img_dir+filters[i]+"/broadband_"+str(gal_id)+'.fits_'+filters[i]+"_band.fits" for i in range(len(filters))]
  #Stack the bands together
  im=[fits.getdata(filename, ext=0) for filename in filenames]
  im_size = min([min(i.shape) for i in im])
  im = np.stack([i[:im_size, :im_size] for i in im], axis=-1).astype('float32')
  return im

#######################


# Markdown description  that will appear on the catalog page.
_DESCRIPTION = """
Creates a tf dataset from Illustris TNG100 NOISELESS images.
"""

# TODO(tng100_images): BibTeX citation
_CITATION = """
"""

class Tng100ImagesNoiseless(tfds.core.GeneratorBasedBuilder):
  """DatasetBuilder for tng100_images dataset."""

  VERSION = tfds.core.Version('1.0.0')
  RELEASE_NOTES = {
      '1.0.0': 'Initial release.',
  }

  def _info(self) -> tfds.core.DatasetInfo:
    """Returns the dataset metadata."""
    # Specifies the tfds.core.DatasetInfo object
    return tfds.core.DatasetInfo(
        builder=self,
        description=_DESCRIPTION,
        features=tfds.features.FeaturesDict({
            # These are the features of the dataset
            'image': tfds.features.Tensor(shape=(128, 128, 4),dtype=tf.float32),
            'last_major_merger': tf.float32,
            "object_id":tf.int32,
        }),
        # If there's a common (input, target) tuple from the
        # features, specify them here. They'll be used if
        # `as_supervised=True` in `builder.as_dataset`.
        supervised_keys=("image","last_major_merger"),
        homepage='https://dataset-homepage/',
        citation=_CITATION,
    )

  def _split_generators(self, dl_manager: tfds.download.DownloadManager):
    """Returns SplitGenerators."""
    #For Jean Zay, change the paths
    data_path = os.path.expandvars("$ALL_CCFRWORK/SFH/tng100/")
    snaps_dir = os.path.join(os.path.dirname(__file__), './')
    #For local test
    #data_path="/content/data"
    #snaps_dir="/content/drive/MyDrive/Colab Notebooks"
    cat_snapshot_path=snaps_dir+"/snap2lookback.csv"
    cat_merger_path=data_path+"/mergers/TNG100_SDSS_MajorMergers.csv"
    img_dir=data_path+"/images/TNG100/sdss/sn99/noiseless/"

    return [
        tfds.core.SplitGenerator(
            name=tfds.Split.TRAIN,
            # These kwargs will be passed to _generate_examples
            gen_kwargs={"img_dir":img_dir,"cat_snapshot_path":cat_snapshot_path,"cat_merger_path":cat_merger_path},
        ),
    ]

  def _generate_examples(self,img_dir=None,cat_snapshot_path=None,cat_merger_path=None):
    """Yields examples."""
    # Yields (key, example) tuples from the dataset
    catalog_merger_time=pd.read_csv(cat_merger_path)
    catalog_snapshot=pd.read_csv(cat_snapshot_path)

    # Get the IDs of the galaxies
    files=os.listdir(img_dir)
    #Remove the names of the directories g,r,i,z
    files.remove('g')
    files.remove('r')
    files.remove('i')
    files.remove('z')

    gal_ids=[int((filename.split("_")[1]).split(".fits")[0]) for filename in files]

    for i in range(len(gal_ids)):
      try:
        #Stacks the bands
        img=stack_bands(img_dir,gal_ids[i])
        #Retrieves the lookback time of the last major merger
        num_last_merger=int(catalog_merger_time[catalog_merger_time["Illustris_ID"]==gal_ids[i]]["SnapNumLastMajorMerger"])
        #Some galaxies have empty values for the lookback time. In such cases, we set the lbt to negative value and then we do not yield these galaxies
        try:
            lbt=float(catalog_snapshot[catalog_snapshot["Snapshot"]==num_last_merger]["Lookback"])
        except:
            lbt=-42
        #Returns the image, the galaxy ID and the lookback time of the last major merger
      except:
          print("Problem for gal_ids",gal_ids[i])
          continue

      if lbt>0:
        yield i, {"image":img.astype("float32"),
                        "last_major_merger":lbt,
                      "object_id":gal_ids[i]}
