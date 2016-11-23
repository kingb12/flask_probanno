import models.model as model
import cobra
import os


def load_model(filename):
    # load model w/ cobra
    mdl = cobra.io.load_json_model(filename)
    model.save(mdl)
