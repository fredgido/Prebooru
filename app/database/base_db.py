# APP/DATABASE/BASE_DB.PY

from .. import SESSION

# ##GLOBAL VARIABLES


def UpdateColumnAttributes(item, attrs, dataparams):
    print("UpdateColumnAttributes", item, attrs, dataparams)
    is_dirty = False
    for attr in attrs:
        print(getattr(item, attr) != dataparams[attr], getattr(item, attr), dataparams[attr])
        if getattr(item, attr) != dataparams[attr]:
            print("Setting basic attr:", attr, dataparams[attr])
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


def UpdateRelationshipCollections(item, relationships, updateparams):
    """For updating multiple values to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(updateparams[attr]).difference(current_values)
        for value in add_values:
            print("Adding collection item:", attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(updateparams[attr])
        for value in remove_values:
            print("Removing collection item:", attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            collection.remove(remove_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


def AppendRelationshipCollections(item, relationships, updateparams):
    """For appending a single value to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        if updateparams[attr] not in current_values:
            value = updateparams[attr]
            print("Adding collection item:", attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
            collection.append(add_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty
