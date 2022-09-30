#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import sys


def progressbar(it, prefix="", size=60, out=sys.stdout):  # Python3.6+
    count = len(it)

    def show(j):
        x = int(size * j / count)
        # print(f"{prefix}{u'█' * x}{('.' * (size - x))} {j}/{count}", end='\r', file=out, flush=True)

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    # print("\n", flush=True, file=out)


from functools import wraps


def decorate_signature(connection):
    def cls_wrapper(cls):
        # You don't have to use wraps, in this case it is a matter of taste.
        # In my opinion using wraps is etiquette usually.
        @wraps(cls)
        def wrapper(*args, **kwargs):
            init_fields = {}
            # Get the field names from the connection class.
            required_fields = connection.__annotations__.keys()
            # print(f'required fields: {list(required_fields)}')
            for field in required_fields:

                # If the field is in kwargs, everything is fine.
                if field in kwargs.keys():
                    init_fields[field] = kwargs[field]

                # A condition if you want to use some default field values.
                elif field in connection.__dict__.keys():

                    init_fields[field] = connection.__dict__[field]

                # Condition if the value of the field, has been missed.
                else:
                    raise f"The required field is lost"

            # If you want to pass new parameters into the function that are not in the connection class.
            kwargs |= init_fields

            # If you want to pass only the fields that are in the connection, use this construction:
            # obj = cls(*args, **init_fields)
            obj = cls(*args, **kwargs)
            return obj

        return wrapper

    return cls_wrapper
