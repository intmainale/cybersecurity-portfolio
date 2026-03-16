from uuid import uuid4

def generate_tracking_links():
    links_map = {}
    with open("campaign_data/users.csv", "r") as file:
        file.readline()
        for line in file.readlines():
            _, email = line.split(",") # name, email
            user_id = uuid4()
            links_map[email] = (f"http://localhost:5000/track?id={user_id}&action=mail_opened", 
                                f"http://localhost:5000/track?id={user_id}&action=no_report", 
                                f"http://localhost:5000/track?id={user_id}&action=report")
    file.close()

    return links_map