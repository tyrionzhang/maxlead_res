"""
print(item['category_rank'])

            rank_el = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(3) td span span::text').extract()
            rank_el1 = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(9) td span span::text').extract()
            rank_el2 = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(7) td span span::text').extract()
            if rank_el and not item['category_rank']:
                if response.css('table#productDetails_detailBullets_sections1 tr:nth-child(3) th::text').extract_first() \
                        .replace('\n', '').strip() == 'Best Sellers Rank':
                    item['category_rank'] = rank_el[0].split(' (')[0]
                    rank_span = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(3) td span span')
                    for n,rank_a in enumerate(rank_span,0):
                        if not n==0:
                            a = rank_a.css('a::text').extract()
                            for s,val in enumerate(a,1):
                                if s == len(a):
                                    item['category_rank'] += val
                                elif s == 1:
                                    item['category_rank'] += '|' + rank_el[2] + val + ' > '
                                else:
                                    item['category_rank'] += val + ' > '
            elif rank_el1 and not item['category_rank']:
                if response.css('table#productDetails_detailBullets_sections1 tr:nth-child(9) th::text').extract_first() \
                        .replace('\n', '').strip() == 'Best Sellers Rank':
                    item['category_rank'] = rank_el1[0].split(' (')[0]
                    rank_span = response.css(
                        'table#productDetails_detailBullets_sections1 tr:nth-child(9) td span span')
                    for n, rank_a in enumerate(rank_span, 0):
                        if not n == 0:
                            a = rank_a.css('a::text').extract()
                            for s, val in enumerate(a, 1):
                                if s == len(a):
                                    item['category_rank'] += val
                                elif s == 1:
                                    item['category_rank'] += '|' + rank_el1[2] + val + ' > '
                                else:
                                    item['category_rank'] += val + ' > '
            elif rank_el2 and not item['category_rank']:
                if response.css('table#productDetails_detailBullets_sections1 tr:nth-child(7) th::text').extract_first()\
                                                                .replace('\n', '').strip() == 'Best Sellers Rank':
                    rank_el = response.css(
                        'table#productDetails_detailBullets_sections1 tr:nth-child(7) td span span::text').extract()
                    if rank_el:
                        item['category_rank'] = rank_el[0].split(' (')[0]
                        rank_span = response.css(
                            'table#productDetails_detailBullets_sections1 tr:nth-child(7) td span span')
                        for n, rank_a in enumerate(rank_span, 0):
                            if not n == 0:
                                a = rank_a.css('a::text').extract()
                                for s, val in enumerate(a, 1):
                                    if s == len(a):
                                        item['category_rank'] += val
                                    elif s == 1:
                                        item['category_rank'] += '|' + rank_el[2] + val + ' > '
                                    else:
                                        item['category_rank'] += val + ' > '
            elif not item['category_rank'] and response.css(
                        'table#productDetails_detailBullets_sections1 tr:nth-child(6) td span span::text').extract():

                rank_span = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(6) td span span')
                a = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(6) td span span::text').extract()
                item['category_rank'] = a[0].split(' (')[0]
                for n, rank_a in enumerate(rank_span, 0):
                    if not n == 0:
                        a = rank_a.css('a::text').extract()
                        for s, val in enumerate(a, 1):
                            if s == len(a):
                                item['category_rank'] += val
                            elif s == 1:
                                item['category_rank'] += '|' + a[2] + val + ' > '
                            else:
                                item['category_rank'] += val + ' > '
"""