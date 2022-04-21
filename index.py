from IPython.display import display
from PIL import Image
import random
import json
import os

os.system('cls' if os.name == 'nt' else 'clear')


def create_new_image(all_images, config):
    new_image = {}

    # Random NFT image traits
    # new_image["Background"] = "Blue Demon"
    for layer in config["layers"]:
        trait = random.choices(layer["values"], layer["weights"])[0]
        new_image[layer["name"]] = trait

    # Check image incompatibility config
    for incomp in config["incompatibilities"]:
        if (new_image[incomp["layer"]] in incomp["values"]):
            common_keys = new_image.keys() & incomp["incompatible_with"].keys()
            if len(common_keys) > 0:
                for key in common_keys:
                    if new_image[key] in incomp["incompatible_with"][key]:
                        return create_new_image(all_images, config)

    if new_image in all_images:
        return create_new_image(all_images, config)
    else:
        return new_image


def generate_unique_images(amount, config):
    print("Generating {} unique NFTs...".format(amount))
    pad_amount = len(str(amount))

    # Prepare trait files reference:
    # trait_files["Background"]["Blue Demon"] = "Blue Demon"  # file name
    trait_files = {}
    for trait in config["layers"]:
        trait_files[trait["name"]] = {}

        for x, key in enumerate(trait["values"]):
            trait_files[trait["name"]][key] = trait["filename"][x]

    # Generate NFT image traits
    all_images = []
    for i in range(amount):
        new_trait_image = create_new_image(all_images, config)
        all_images.append(new_trait_image)

    # Assign token ID to NFT image traits
    i = 1
    for item in all_images:
        item["tokenId"] = i
        i += 1

    # Generate individual NFT meta data json file
    for i, token in enumerate(all_images):
        attributes = []
        for key in token:
            if key != "tokenId" and token[key] != "NIL":
                attributes.append({"trait_type": key, "value": token[key]})

        token_metadata = {
            "image": config["baseURI"] + "/images/" + str(token["tokenId"]) + '.png',
            "tokenId": token["tokenId"],
            "name":  config["name"] + " " + str(token["tokenId"]).zfill(pad_amount),
            "description": config["description"],
            "attributes": attributes
        }
        with open('./metadata/' + str(token["tokenId"]) + '.json', 'w') as outfile:
            json.dump(token_metadata, outfile, indent=4)

    # Dump all NFTs meta data json file
    with open('./metadata/all-objects.json', 'w') as outfile:
        all_images_nonil = []
        for image in all_images:
            all_images_nonil.append({key: value for (key, value)
                                     in image.items() if value != "NIL"})
        json.dump(all_images_nonil, outfile, indent=4)

    # Generate NFT images
    for item in all_images:
        # remove the NIL value attr
        item_nonil = {key: value for (
            key, value) in item.items() if value != "NIL"}

        layers = []
        for index, attr in enumerate(item_nonil):
            if attr != "tokenId":
                layers.append([])
                layer_config = [e for e in config["layers"]
                                if e['name'] == attr][0]
                path = layer_config["trait_path"]
                image_file = trait_files[attr][item_nonil[attr]]
                layers[index] = Image.open(
                    f'{path}/{image_file}.png').convert('RGBA')

        if len(layers) == 1:
            rgb_im = layers[0].convert('RGBA')
            file_name = str(item["tokenId"]) + ".png"
            rgb_im.save("./images/" + file_name)
        elif len(layers) == 2:
            main_composite = Image.alpha_composite(layers[0], layers[1])
            rgb_im = main_composite.convert('RGBA')
            file_name = str(item["tokenId"]) + ".png"
            rgb_im.save("./images/" + file_name)
        elif len(layers) >= 3:
            main_composite = Image.alpha_composite(layers[0], layers[1])
            layers.pop(0)
            layers.pop(0)
            for index, remaining in enumerate(layers):
                main_composite = Image.alpha_composite(
                    main_composite, remaining)
            rgb_im = main_composite.convert('RGBA')
            file_name = str(item["tokenId"]) + ".png"
            rgb_im.save("./images/" + file_name)

    # v1.0.2 addition
    print("\nUnique NFT's generated. After uploading images to IPFS, please paste the CID below.\nYou may hit ENTER or CTRL+C to quit.")
    cid = []  # input("IPFS Image CID (): ")
    if len(cid) > 0:
        if not cid.startswith("ipfs://"):
            cid = "ipfs://{}".format(cid)
        if cid.endswith("/"):
            cid = cid[:-1]
        for i, item in enumerate(all_images):
            with open('./metadata/' + str(item["tokenId"]) + '.json', 'r') as infile:
                original_json = json.loads(infile.read())
                original_json["image"] = original_json["image"].replace(
                    config["baseURI"]+"/", cid+"/")
                with open('./metadata/' + str(item["tokenId"]) + '.json', 'w') as outfile:
                    json.dump(original_json, outfile, indent=4)


with open('config.json') as json_file:
    config = json.load(json_file)

generate_unique_images(100, config)

# Additional layer objects can be added following the above formats. They will automatically be composed along with the rest of the layers as long as they are the same size as eachother.
# Objects are layered starting from 0 and increasing, meaning the front layer will be the last object. (Branding)
