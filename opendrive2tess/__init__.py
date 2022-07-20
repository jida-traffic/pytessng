def send_signal(context, value, network_info=None, error=False):
    if not (context and context.get("signal") and context.get("pb")):
        return

    signal = context["signal"]
    pb = context["pb"]
    network_info = network_info or {}
    signal.emit(pb, value, network_info, error)
