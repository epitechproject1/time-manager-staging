import threading


def run_async(func, *args, **kwargs):
    """
    Lance une fonction en arrière-plan (non bloquant).
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
