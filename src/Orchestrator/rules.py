from flask import Blueprint
from flask import abort
from flask import jsonify
from flask import request
import time


from src.Orchestrator.utils import BACK_OFF_TIME_MS, MAX_TRIES, get_db

rules_routes = Blueprint('rules', __name__)


def retrieve_rule(rule_name):
    try:
        return get_db().get_rule(rule_name)
    except ValueError:
        return abort(404)


@rules_routes.route("/rule/<rule_name>", methods=['GET'])
def get_rule(rule_name):
    return jsonify(retrieve_rule(rule_name))


@rules_routes.route("/rule/", methods=['GET'])
def get_rules():
    return jsonify(get_db().get_rules())


@rules_routes.route("/rule/<rule_name>/activate", methods=['PUT'])
def activate_rule(rule_name):
    put_done = False
    tries = 0
    while not put_done:
        tries += 1
        rule = retrieve_rule(rule_name)
        rule["active"] = True
        get_db().update_rule(rule)
        rule = retrieve_rule(rule_name)

        time.sleep(BACK_OFF_TIME_MS / 1000)
        put_done = rule["active"]
        if tries >= MAX_TRIES:
            return abort(400, {"message": "MAX_TRIES updating database document"})
    return jsonify(201)


@rules_routes.route("/rule/<rule_name>/deactivate", methods=['PUT'])
def deactivate_rule(rule_name):
    put_done = False
    tries = 0
    while not put_done:
        tries += 1
        rule = retrieve_rule(rule_name)
        rule["active"] = False
        get_db().update_rule(rule)

        time.sleep(BACK_OFF_TIME_MS / 1000)
        rule = retrieve_rule(rule_name)
        put_done = not rule["active"]
        if tries >= MAX_TRIES:
            return abort(400, {"message": "MAX_TRIES updating database document"})
    return jsonify(201)


@rules_routes.route("/rule/<rule_name>/amount", methods=['PUT'])
def change_amount_rule(rule_name):
    put_done = False
    tries = 0
    try:
        amount = int(request.json["value"])
    except KeyError:
        return abort(400)

    while not put_done:
        tries += 1
        rule = retrieve_rule(rule_name)
        rule["amount"] = amount
        get_db().update_rule(rule)

        time.sleep(BACK_OFF_TIME_MS / 1000)
        rule = retrieve_rule(rule_name)
        put_done = rule["amount"] == amount
        if tries >= MAX_TRIES:
            return abort(400, {"message": "MAX_TRIES updating database document"})
    return jsonify(201)

@rules_routes.route("/rule/<rule_name>/policy", methods=['PUT'])
def change_policy_rule(rule_name):
    rule = retrieve_rule(rule_name)

    if rule["generates"] == "requests" and rule["rescale_type"] == "up":
        put_done = False
        tries = 0

        rescale_policy = request.json["value"]
        if rescale_policy not in ["amount", "proportional"]:
            return abort(400, {"message": "Invalid policy"})
        else:
            while not put_done:
                tries += 1
                rule = retrieve_rule(rule_name)
                rule["rescale_policy"] = rescale_policy
                get_db().update_rule(rule)

                time.sleep(BACK_OFF_TIME_MS / 1000)
                rule = retrieve_rule(rule_name)
                put_done = rule["rescale_policy"] == rescale_policy
                if tries >= MAX_TRIES:
                    return abort(400, {"message": "MAX_TRIES updating database document"})
        return jsonify(201)
    else:
        return abort(400, {"message": "This rule can't have its policy changed"})