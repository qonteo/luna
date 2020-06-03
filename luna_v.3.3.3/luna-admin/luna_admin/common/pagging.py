def pageCount(countItems, pageSize):
    return int((countItems + pageSize - 1) / pageSize)


def getPages(page, pageSize, countItems):
    maxPage =pageCount(countItems, pageSize)
    paging = {"page": str(page), "prev_page":  str(max(1, page - 1)),
              "next_page": str(min(maxPage, page + 1)), "max_page": str(max(maxPage,1)),
              "page_size":str(pageSize)}
    return paging