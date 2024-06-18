from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    jsonify,
    json,
)
import os, random, fnmatch

app = Flask(__name__)

# Replace with your actual image directory path
IMAGE_DIR = os.getenv("IMAGE_DIR", "test-images")

# In-memory store for image click counts and Elo ratings
# Initialize all images with a rating of 1200
# Only incude files elding in *.png
image_data = {
    image: {"clicks": 0, "elo": 1200}
    for image in os.listdir(IMAGE_DIR)
    if fnmatch.fnmatch(image, "*.png")
}

# Load Elo ratings from a json file if it exists

# Determine path to the json file by combining the image directory with the filename
elo_file = os.path.join(IMAGE_DIR, "elo_ratings.json")

if os.path.exists(elo_file):
    with open(elo_file, "r") as f:
        sorted_image_data = json.load(f)
        image_data = {
            image: {"clicks": data["clicks"], "elo": data["elo"]}
            for image, data in sorted_image_data
        }


@app.route("/")
def index():
    image_files = list(image_data.keys())
    # Create a list of weights based on the Elo ratings
    weights = [image_data[image]["elo"] for image in image_files]
    # Use the weights when picking two images
    images = random.choices(image_files, weights=weights, k=2)
    
    # Check if the same image was picked twice
    while images[0] == images[1]:
        images = random.choices(image_files, weights=weights, k=2)
    
    print(images)
    return render_template("index.html", images=images)


@app.route("/images/<filename>")
def send_image(filename):
    return send_from_directory(IMAGE_DIR, filename)


@app.route("/record_click", methods=["POST"])
def record_click():
    winner = request.json["winner"]
    loser = request.json["loser"]

    # Increment click count for the winner
    image_data[winner]["clicks"] += 1

    # Update Elo ratings
    winner_rating = image_data[winner]["elo"]
    loser_rating = image_data[loser]["elo"]

    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loser = 1 - expected_winner

    k = 32
    new_winner_rating = winner_rating + k * (1 - expected_winner)
    new_loser_rating = loser_rating + k * (0 - expected_loser)

    image_data[winner]["elo"] = new_winner_rating
    image_data[loser]["elo"] = new_loser_rating

    print(
        f"Image {winner} has been clicked {image_data[winner]['clicks']} times and has an Elo rating of {image_data[winner]['elo']}."
    )

    # store the elo ratings in a json file in human-readable format
    # sorted by elo rating
    with open(elo_file, "w") as f:
        sorted_image_data = sorted(
            image_data.items(), key=lambda item: item[1]["elo"], reverse=True
        )
        json.dump(sorted_image_data, f, indent=4, sort_keys=True)

    # print the image rankings sorted by elo rating
    print("Image rankings:")
    for image, data in sorted(
        image_data.items(), key=lambda x: x[1]["elo"], reverse=True
    ):
        print(f"{image}: Elo rating {data['elo']}")

    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)
