# SessionPath (Ludwig re-mastered edition)
_Personalized Category Suggestions for eCommerce Type-Ahead_


### Overview
This repo contains working code from our blog post
[Building personalized category suggestions with Ludwig](https://blog.coveo.com/clothes-in-space-real-time-personalization-in-less-than-100-lines-of-code/).
By leveraging [Ludwig](https://uber.github.io/ludwig/api/LudwigModel/) capabilities, we implement an encoder-decoder architecture
to provide personalized and dynamic _category suggestion_ to augment type-ahead API. 

A typical type-ahead experience is this one:

![Amazon Category Suggestion Example](/images/amazon.png)

What we are trying to build is a _smarter_ system, one that suggests different categories depending on contextual
factors as well (e.g. the products the user interacted with):

![Dynamic Category Suggestion Example](/images/personalized_category.jpg)

Blog post and code are inspired by our [research paper](https://arxiv.org/abs/2005.12781) presented @ ACL 2020: 
[How to Grow a (Product) Tree](https://blog.coveo.com/clothes-in-space-real-time-personalization-in-less-than-100-lines-of-code/).

### Setup

Code has been written for Python 3.7 - the provided `requirements.txt` can be used with a [virtualenv](https://virtualenv.pypa.io/en/latest/)
to run the project in a separate virtual environment. 

Credentials and global parameters can be set with the standard `.env` file (`*.env.local` is provided as a template), and 
they are available in the pipeline script through [dotenv](https://pypi.org/project/python-dotenv/).


### Repo Structure

We provide two main scripts to test out our models for category prediction in type-ahead:
a simplified, but realistic end-to-end "stateless" pipeline, creating from scratch
 from raw data all input features and a Ludwig-friendly dataset; a stand-alone folder
 with a minimal Ludwig script in case you already have embeddings and data rows ready for the model.

#### Luigi-powered pipeline
By running `model_pipeline.py`, a [Luigi](https://github.com/spotify/luigi) local pipeline executes a DAG comprising
four tasks:

* _prod2vec_ training: product embeddings are trained from browsing data and stored locally as text in the Glove format;
* dataset preparation: extract data from search logs and prepare a csv with three columns,
 "query" (the input query), "skus_in_session" (product identifiers for in-session interactions: view, add, etc.),
 "path" (the target taxonomy path). "skus_in_session" and "path" are sequences, so they are saved as tokens separated
 by a space;
* Ludwig training: define the deep learning model and feed it to Ludwig for training and local persistence;
* Ludwig testing: load the model from storage, test it on held-out data and print out summary statistics.

By using Luigi, we wrap this DAG in a convenient flow that saves us time if we need to re-run the pipeline 
from a particular step, and ensure consistency if we perform a clean run.

Please note that data retrieval functions in `data_service.py` and `prod2vec_train.py` are just stubs: 
in our original repository they contained our Snowflake-based code to load behavioral 
and search data from our warehouse; modify them with your own logic to extract behavioral and search data so that
downstream tasks can run seamlessly (we left a small snowflake client in the repo for convenience).

The folder `ludwig_playground` contains `*.local` files that show sample datasets and sample ancillary files.

The folder `data` contains `catalog.csv.local`, which is a sample `csv` file 
representing product information (identifiers, images,
taxonomy path): it may be useful to have a product lookup 
if your search logs (e.g. products clicked after a search) report product identifiers and you need to join
products with paths to prepare the final dataset.

#### Standalone Ludwig training
If you already have embeddings ready (stored in a tab-separated text file, as in 
the ["Glove format"](https://radimrehurek.com/gensim/scripts/glove2word2vec.html)) and a dataset file, you can put them in the `ludwig_playground`
folder and play directly with Ludwig code with no other dependency: `ludwig_playground.py` have some global variables
you can set to re-run training, or just running a trained model on new input rows.

The `*.local` files in the folder show the accepted format for a dataset and an embedding file to run the Ludwig code.

### Acknowledgments
This repo is a joint effort of [Jacopo](http://www.jacopotagliabue.it/), 
[Bingqing](https://www.linkedin.com/in/bingqing-christine-yu/)
 and [Marie](https://www.linkedin.com/in/marie-beaulieu-462949135/). 

We wish to thank our friend [Piero Molino](https://github.com/w4nderlust), 
[Ludwig](https://uber.github.io/ludwig/)'s creator, for showing
us how to re-write our model (_SessionPath_) with Ludwig. 

### How to Cite our Work

If you find this repo (and the ideas in it) useful for your research, please cite our
[ECNLP](https://sites.google.com/view/ecnlp/acl-2020?authuser=0) work @ ACL:

Jacopo Tagliabue, Bingqing Yu, Marie Beaulieu, 2020, 
"How to Grow a (Product) Tree: Personalized Category Suggestions for eCommerce Type-Ahead",
Companion Proceedings of ACL 2020, Seattle, US.

The arxiv version is available [here](https://arxiv.org/abs/2005.12781).

### License
The code in this repo is freely available and provided "as is" as covered by the [MIT License](https://opensource.org/licenses/MIT).
