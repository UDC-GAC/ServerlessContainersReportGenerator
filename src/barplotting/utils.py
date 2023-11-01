def get_y_limit(plotting_method, max_y_limit, benchmark_type=None, resource_label=None, static_limits=False):
    limit = max_y_limit * cfg.Y_AMPLIFICATION_FACTOR
    top, bottom = (limit, 0)
    return top, bottom