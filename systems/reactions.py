def react(event):

    responses = {
        "hell": "☠️ Sent to #HELL.",
        "deny": "Mercy was considered… and rejected.",
        "accept": "Mercy granted.",
        "no_permission": "You are not authorized to invoke SeiTan."
    }

    return responses.get(event, "SeiTan observes.")