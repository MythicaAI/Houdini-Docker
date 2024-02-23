import logging
import os

import docker
from docker.errors import NotFound
from sesiweb import SesiWeb
from sesiweb.model.service import BuildDownloadModel, DailyBuild, ProductBuild

import hbuild.util.logutils as logutils
import hbuild.util.workflowutils as wfutils

logging.basicConfig(level=logging.INFO)

EULA_DATE = "2021-10-13"

DOCKER_USER = os.environ.get("DOCKER_USER")
DOCKER_SECRET = os.environ.get("DOCKER_SECRET")
DOCKER_REPO = os.environ.get("DOCKER_REPO")

SIDEFX_CLIENT = os.environ.get("SIDEFX_CLIENT")
SIDEFX_SECRET = os.environ.get("SIDEFX_SECRET")

install_dir = "../hinstall"
build_repo = f"{DOCKER_USER}/{DOCKER_REPO}"


def image_tag_exists(docker_client: docker.DockerClient, tag: str, repo: str) -> bool:
    try:
        server_image = docker_client.images.pull(repository=repo, tag=tag)
    except NotFound as e:
        logging.debug(f"Error `{e}` raised pulling server image")
        server_image = None
    if server_image:
        logging.info(f"Upload not needed, image tag `{tag}` already exists")
        return False
    logging.info("Tag does not exist in repository, beginning download/push process...")
    return True


def get_latest_build(
    sw_product: str = "houdini", sw_platform: str = "linux"
) -> (BuildDownloadModel, DailyBuild):
    logging.info("Starting Houdini download client service")

    sw = SesiWeb(client_secret=SIDEFX_SECRET, client_id=SIDEFX_CLIENT)

    product_build = {"product": sw_product, "platform": sw_platform}

    build_select = sw.get_latest_build(prodinfo=product_build)

    build_dl = sw.get_build_download(prodinfo=ProductBuild(**build_select.dict()))

    return build_dl, build_select


if __name__ == "__main__":
    client = docker.from_env()

    build_url, build_meta = get_latest_build()

    build_tag = f"{build_meta.version}.{build_meta.build}-base"
    logging.info(f"Latest build found: `{build_tag}`")

    tag_status = image_tag_exists(docker_client=client, tag=build_tag, repo=build_repo)

    if tag_status:
        build_args = {
            "DL_URL": build_url.download_url,
            "DL_NAME": build_url.filename,
            "DL_HASH": build_url.hash,
            "EULA_DATE": EULA_DATE,
        }

        dockerfile_dir = os.path.join(os.path.dirname(__file__), "..", "hinstall")

        logging.info("Building Docker image...")
        image, logs = client.images.build(
            path=os.path.abspath(dockerfile_dir),
            rm=True,
            nocache=True,
            tag=f"{build_repo}:{build_tag}",
            buildargs=build_args,
            encoding="gzip",
        )

        logging.info(f"Built Docker image `{image.short_id}`, pushing to Docker hub...")
        client.login(username=DOCKER_USER, password=DOCKER_SECRET)

        for line in client.images.push(
            repository=build_repo, tag=build_tag, stream=True
        ):
            logutils.process_docker_message(line)
        logging.info(f"Pushed Docker image `{build_tag}` in `{build_repo}`.")

        docker.from_env().images.get(f"{build_repo}:{build_tag}").tag(
            f"{build_repo}:latest"
        )

        for line in client.images.push(
            repository=build_repo, tag="latest", stream=True
        ):
            logutils.process_docker_message(line)
        logging.info(f"Pushed Docker image `latest` in `{build_repo}`.")
        wfutils.actions_write_output(name="test_status", value="cont")
    else:
        wfutils.actions_write_output(name="test_status", value="skip")

    logging.info("Finished HouDocker process, exiting...")
