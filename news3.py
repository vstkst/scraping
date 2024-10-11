import requests
import json
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Define your cookies
cookies = {
    '_ga': 'GA1.1.1158334649.1728365709',
    'OptanonAlertBoxClosed': '2024-10-08T05:40:51.230Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Oct+09+2024+16%3A01%3A17+GMT%2B0530+(India+Standard+Time)&version=202407.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0002%3A1%2CC0004%3A1%2CC0001%3A1&geolocation=IN%3BTN&AwaitingReconsent=false',
    '_ga_FPMRD799QM': 'GS1.1.1728462353.6.1.1728469881.0.0.0',
    'AWSALB': 'oGKCjpUo0wld6OhTlXO2Wdhkl5/CQF2BAX/jAtcw7PSFWmzfYsb5zthWnA9dyWVp056CSPV3qt51fwX5rViifo9PR4MkL3i0y4kpqD2gXpLNrNdPfRzY6DJlYY1s',
    'AWSALBCORS': 'oGKCjpUo0wld6OhTlXO2Wdhkl5/CQF2BAX/jAtcw7PSFWmzfYsb5zthWnA9dyWVp056CSPV3qt51fwX5rViifo9PR4MkL3i0y4kpqD2gXpLNrNdPfRzY6DJlYY1s',
}

# Define your headers
headers = {
    'accept': '*/*',
    'accept-language': 'en-IN,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,en-GB;q=0.6,en-US;q=0.5',
    'cache-control': 'no-cache',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://www.elite.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.elite.com/news/',
    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
}

# Function to clean content text
def clean_content(content):
    # Remove Unicode characters like \u201c and HTML tags
    content_cleaned = re.sub(r'\\u201[c|d]', '"', content)  # Replace curly quotes with straight quotes
    content_cleaned = re.sub(r'<.*?>', '', content_cleaned)  # Remove HTML tags
    content_cleaned = re.sub(r'\s+', ' ', content_cleaned).strip()  # Remove extra whitespaces
    return content_cleaned

# List to store extracted data for each post
extracted_data = []

# Iterate through offsets from 0 to 41 (inclusive)
for offset in range(42):  # 0 to 41
    # Update the data payload with the new offset
    data = f'{{"postType":"news","filters":{{"product":"all","region":"all","news_category":"all"}},"offset":{offset}}}'
    
    # Make the POST request to get the list of posts
    response = requests.post('https://www.elite.com/api/collection/', cookies=cookies, headers=headers, data=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Extract the JSON data from the response
        json_data = response.json()
        
        # Navigate inside the posts and extract the URL for Post 0 only
        posts = json_data.get('posts', [])
        if posts:
            url = posts[0].get('url', 'No URL found')  # Only extract Post 0
            print(f"Offset {offset}, Post 0: {url}")

            # Now make a GET request to the extracted URL
            url_response = requests.get(url)
            
            if url_response.status_code == 200:
                # Parse the response content using BeautifulSoup
                soup = BeautifulSoup(url_response.content, 'html.parser')
                
                # Find the script tag with id="__NEXT_DATA__"
                script_tag = soup.find('script', id="__NEXT_DATA__", type="application/json")
                
                if script_tag:
                    # Extract the JSON data
                    script_json = json.loads(script_tag.string)
                    
                    # Traverse the JSON to get the required data points
                    try:
                        news_data = script_json['props']['pageProps']['data']['newsArticle']
                        title = news_data['title']
                        image_url = news_data['featuredImage']['node']['sourceUrl']
                        article_url = news_data['seo']['canonical']
                        
                        # Extract full content from the blocks and clean it
                        blocks = news_data.get('blocks', [])
                        full_content = ""
                        for block in blocks:
                            attributes_json = block.get('attributesJSON')
                            if isinstance(attributes_json, str):
                                block_data = json.loads(attributes_json)
                                content = block_data.get('content', '')
                                clean_text = clean_content(content)
                                full_content += clean_text + " "
                        
                        # Find the datePublished in the 'raw' field and extract only the date
                        raw_data = news_data['seo']['schema']['raw']
                        raw_json = json.loads(raw_data)
                        date_published = "Not available"
                        for item in raw_json.get('@graph', []):
                            if 'datePublished' in item:
                                date_published = item['datePublished'][:10]  # Extract only the date part
                        
                        # Construct the final data dictionary in the desired order
                        post_data = {
                            "article_url": article_url,
                            "collected_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date and time
                            "full_content": full_content.strip(),
                            "response_code": url_response.status_code,  # Response code of the generated URL
                            "topic_url": "https://www.elite.com/news/law",  # Assuming constant URL
                            "image_url": image_url,
                            "title": title,
                            "source_link": "https://www.elite.com/news/law",  # Assuming constant URL
                            "published_date": date_published  # Extracted published date
                        }
                        
                        # Append the extracted data to the list
                        extracted_data.append(post_data)
                        print(f"Extracted data for Offset {offset}, Post 0:")
                        print(post_data)
                    except KeyError as e:
                        print(f"Error traversing JSON for Offset {offset}, Post 0: {e}")
                else:
                    print(f"No script tag with id '__NEXT_DATA__' found for URL {url}")
            else:
                print(f"Failed to fetch content for URL {url}, Status code: {url_response.status_code}")
        print("\n" + "="*50 + "\n")  # Separator for readability
    else:
        print(f"Failed to fetch data for offset {offset}, Status code: {response.status_code}")

# Save extracted data to JSON
with open('extracted_data.json', mode='w', encoding='utf-8') as file:
    json.dump(extracted_data, file, indent=4, ensure_ascii=False)

print("Data extraction completed and saved to extracted_data.json")
