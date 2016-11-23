import data.database as db
import controllers.session_management as session_management
import cobra

def save(model):
    db.insert_model(session_management.get_session_id(), model.name, cobra.io.json.to_json(model))