from flask import render_template

def PageNavigation(paginate, request):
    current_page = paginate.page
    previous_page = paginate.prev_num
    next_page = paginate.next_num
    last_page = paginate.pages
    left = max(current_page - 4, 2)
    penultimate_page = last_page - 1
    right = min(current_page + 4, penultimate_page)
    pages = [1]
    pages += ['...'] if left != 2 else []
    pages += list(range(left, right))
    pages += ['...'] if right != penultimate_page else []
    pages += [last_page] if last_page != 1 else []
    return render_template("paginator.html", prev_page=previous_page, current_page=current_page, next_page=next_page, pages=pages)
