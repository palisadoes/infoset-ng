"""infoset-ng database API. Data table."""

# Standard imports
from datetime import datetime
from collections import defaultdict

# Flask imports
from flask import Blueprint, jsonify, request

# Infoset-ng imports
from infoset.utils import general
from infoset.db import db_agent
from infoset.db import db_data
from infoset.db import db_device
from infoset.db import db_deviceagent
from infoset.db import db_multitable
from infoset.api import CACHE, CONFIG

# Define the LASTCONTACTS global variable
LASTCONTACTS = Blueprint('LASTCONTACTS', __name__)


@LASTCONTACTS.route('/lastcontacts')
@CACHE.cached()
def lastcontacts():
    """Get last contact data from the DB.

    Args:
        None

    Returns:
        data: JSON data for the selected agent

    """
    # Get starting timestamp
    secondsago = general.integerize(request.args.get('secondsago'))
    timestamp = general.integerize(request.args.get('ts_start'))
    if bool(timestamp) is True:
        ts_start = _start_timestamp(timestamp, relative=False)
    else:
        if bool(secondsago) is True:
            ts_start = _start_timestamp(secondsago)
        else:
            secondsago = 3600
            ts_start = _start_timestamp(secondsago)

    # Get data
    data = db_data.last_contacts(ts_start)

    # Return
    return jsonify(data)


@LASTCONTACTS.route('/lastcontacts/id_agents')
@CACHE.cached()
def id_agents():
    """Get last contact data from the DB.

    Args:
        None

    Returns:
        data: JSON data for the selected agent

    """
    # Initialize key variables
    data = []
    outcomes = defaultdict(lambda: defaultdict(dict))

    # Get starting timestamp
    secondsago = general.integerize(request.args.get('secondsago'))
    timestamp = general.integerize(request.args.get('ts_start'))
    if bool(timestamp) is True:
        ts_start = _start_timestamp(timestamp, relative=False)
    else:
        if bool(secondsago) is True:
            ts_start = _start_timestamp(secondsago)
        else:
            secondsago = 3600
            ts_start = _start_timestamp(secondsago)

    # Get the agent ids assigned to each datapoint
    mapping = db_multitable.datapoint_summary()

    # Get the contacts
    contacts = db_data.last_contacts(ts_start)

    # Store the contacts according to id_agent and agent_label
    for contact in contacts:
        data_dict = {
            'timestamp': contact['timestamp'],
            'value': contact['value']}
        idx_datapoint = contact['idx_datapoint']
        id_agent = mapping[idx_datapoint]['id_agent']
        agent_label = mapping[idx_datapoint]['agent_label']
        outcomes[id_agent][agent_label] = data_dict

    # Create a list of dicts of contacts keyed by id_agent
    for id_agent, label_dict in outcomes.items():
        # Initalize dict for id_agent data
        new_dict = defaultdict(lambda: defaultdict(dict))
        for label, value_dict in label_dict.items():
            new_dict[id_agent][label] = value_dict

        # Append dict to data
        data.append(new_dict)

    # Return
    return jsonify(data)


@LASTCONTACTS.route('/lastcontacts/deviceagents/<int:value>')
@CACHE.cached()
def deviceagents(value):
    """Get last contact data from the DB.

    Args:
        value: Index from the DeviceAgent table
        ts_start: Timestamp to start from

    Returns:
        data: JSON data for the selected agent

    """
    # Initialize key variables
    idx_deviceagent = int(value)

    # Get starting timestamp
    secondsago = general.integerize(request.args.get('secondsago'))
    timestamp = general.integerize(request.args.get('ts_start'))
    if bool(timestamp) is True:
        ts_start = _start_timestamp(timestamp, relative=False)
    else:
        ts_start = _start_timestamp(secondsago)

    # Get data
    data = db_data.last_contacts_by_device(idx_deviceagent, ts_start)

    # Return
    return jsonify(data)


@LASTCONTACTS.route(
    'lastcontacts/devicenames/<string:devicename>/id_agents/<string:id_agent>')
@CACHE.cached()
def devicename_agents(devicename, id_agent):
    """Get last contact data from the DB.

    Args:
        devicename: Device table devicename
        id_agent: Agent table id_agent

    Returns:
        data: JSON data for the selected agent

    """
    # Initialize key variables
    data = []

    # Get starting timestamp
    secondsago = general.integerize(request.args.get('secondsago'))
    timestamp = general.integerize(request.args.get('ts_start'))
    if bool(timestamp) is True:
        ts_start = _start_timestamp(timestamp, relative=False)
    else:
        ts_start = _start_timestamp(secondsago)

    # Get idx_device and idx_agent
    device = db_device.GetDevice(devicename)
    if device.exists() is True:
        # Device Found
        idx_device = device.idx_device()

        # Now find idx_agent
        agent = db_agent.GetIDAgent(id_agent)
        if agent.exists() is True:
            idx_agent = agent.idx_agent()

        # Now get the idx_deviceagent
        deviceagent = db_deviceagent.GetDeviceAgent(idx_device, idx_agent)
        if deviceagent.exists() is True:
            idx_deviceagent = deviceagent.idx_deviceagent()

            # Now get the data
            data = db_data.last_contacts_by_device(
                int(idx_deviceagent), int(ts_start))

    # Return
    return jsonify(data)


def _start_timestamp(secondsago=None, relative=False):
    """Determine the default starting timestamp when not provided.

    Args:
        None

    Returns:
        ts_start: Timestamp

    """
    # Provide a UTC timestamp 10x the configured interval
    interval = CONFIG.interval()

    if (bool(secondsago) is False) or (secondsago < 0):
        timestamp = int(datetime.utcnow().timestamp()) - (interval * 10)
    else:
        if bool(relative) is True:
            timestamp = int(datetime.utcnow().timestamp()) - secondsago
        else:
            timestamp = abs(secondsago)

    # Return
    ts_start = general.normalized_timestamp(timestamp)
    return ts_start
