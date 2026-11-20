from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Возвращает страницу списка по параметру ?page=N.

    Некорректные значения заменяются на значения по умолчанию:
    - не число (?page=abc)            -> первая страница;
    - меньше 1 (?page=0, ?page=-3)    -> первая страница;
    - больше числа страниц (?page=999) -> последняя страница.
    """
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        too_small = int(page_number) < 1
        page = paginator.page(1 if too_small else paginator.num_pages)

    # Данные для шаблона пагинатора: номера страниц с многоточием
    # вида [1, 2, '…', 9, 10, 11, '…', 52, 53]
    page.elided_range = list(
        paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)
    )
    return page
