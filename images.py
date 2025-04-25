import base64

from openai import OpenAI


def generate_image(prompt):
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    with open("sample_images/img_0.png", "wb") as f:
        f.write(image_bytes)


def generate_image_from_img(prompt, image_path, output_path):
    result = client.images.edit(
        model="gpt-image-1",
        image=[
            open(image_path, "rb")
        ],
        prompt=prompt
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    # Save the image to a file
    with open(output_path, "wb") as f:
        f.write(image_bytes)



if __name__ == "__main__":    
    client = OpenAI()
    main_character_description = "Create a little girl in the galaxy, she is the main character of the story. She is wearing a pink dress and has long brown hair. She is smiling and looking at the stars."
    fairy_tale_description = "A little girl from the reference image meets a new friend from another galaxy. She remains the same but in a different pose."

    # Generate the first image based on the main character description
    image_response = generate_image(main_character_description)
    image_path = "sample_images/img_0.png"
    image_response = generate_image_from_img(fairy_tale_description, image_path, output_path="sample_images/img_1.png")
