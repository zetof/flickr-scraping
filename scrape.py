import os
import sys
import re
import requests
from bs4 import BeautifulSoup


def get_img_ref(picture_soup):
    img_src = picture_soup.attrs['style']
    return find_img_ref.findall(img_src)[0]


def get_last_img_ref(pictures_soup):
    try:
        last_img = pictures_soup[-1]
        return get_img_ref(last_img)
    except IndexError:
        return 0


if __name__ == '__main__':
    nb_of_args = len(sys.argv)
    if nb_of_args != 3:
        print('Usage: python scrape.py <directory> <album_url>')
        quit()
    for i, arg in enumerate(sys.argv):
        if i == 1:
            output_dir = arg
        if i == 2:
            album_url = arg

    find_img_ref = re.compile(r'\/(\d{11})_')
    find_base_url = re.compile(r'\/photos\/(.+)\/albums')

    base_url = 'https://www.flickr.com/photos/{}'.format(find_base_url.findall(album_url)[0])
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    pictures_page = requests.get(album_url)

    print('\r\n==> Processing album')
    needs_paging = True
    previous_img_ref = 0
    while needs_paging:
        pictures_soup = BeautifulSoup(pictures_page.content, 'html.parser')
        pictures = pictures_soup.find_all('div', class_='photo-list-photo-view')
        last_img_ref = get_last_img_ref(pictures)
        if last_img_ref != 0:
            pictures_page = requests.get('{}/with/{}'.format(album_url, last_img_ref))
            if previous_img_ref != last_img_ref:
                previous_img_ref = last_img_ref
                previous_pictures = pictures
            else:
                needs_paging = False
        else:
            needs_paging = False
            pictures = previous_pictures

    total_ok = 0
    total_fail = 0
    for picture in pictures:
        img_ref = get_img_ref(picture)
        img_path = '{}/{}.jpg'.format(output_dir, img_ref)
        if os.path.isfile(img_path):
            total_ok += 1
            print('    > Picture {} already axists'.format(img_ref))
        else:
            img_sizes_url = '{}/{}{}'.format(base_url, img_ref, '/sizes/l/')
            sizes_page = requests.get(img_sizes_url)
            sizes_soup = BeautifulSoup(sizes_page.content, 'html.parser')
            sizes = sizes_soup.find('ol', class_='sizes-list')
            bigger_sizes = sizes.find_all('li')[-2]
            try:
                biggest_size_url = 'https://flickr.com{}'.format(bigger_sizes.find('a').attrs['href'])
                biggest_page = requests.get(biggest_size_url)
                biggest_soup = BeautifulSoup(biggest_page.content, 'html.parser')
                img_url = biggest_soup.find('div', id='allsizes-photo').find('img').attrs['src']
                img_data = requests.get(img_url).content
                with open(img_path, 'wb') as handler:
                    handler.write(img_data)
                total_ok += 1
                print('    > Picture {} dowloaded'.format(img_ref))
            except AttributeError:
                total_fail += 1
                print('    > Picture {} skipped due to an attribute problem'.format(img_ref))
    print('==> Total downloaded: {} / Total failed: {}'.format(total_ok, total_fail))
