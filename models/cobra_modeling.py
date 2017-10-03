import cobra
import json
import probanno


def model_to_json(model):
    return cobra.io.json.to_json(model)


def from_json_file(filename):
    return cobra.io.load_json_model(filename)


def from_json(model):
    return cobra.io.json.from_json(model)


def solution_to_json(solution):
    return json.dumps({'x': solution.x,
                'y': solution.y,
                'f': solution.f,
                'solver': solution.solver,
                'x_dict': solution.x_dict,
                'y_dict': solution.y_dict
                })


def run_fba(model):
    return model.optimize()


def gapfill_model(model, universal_model, likelihoods):
    return probanno.probabilistic_gapfill(model, universal_model, likelihoods)

def build_universal_model(temlate_file):
    return probanno.build_universal_model(temlate_file, clean_exchange_reactions=True)


def get_universal_model(universal_model_file):
    return cobra.io.json.load_json_model(universal_model_file)
