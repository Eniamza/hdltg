import json


def get_cfg():
    with open('cfg.json') as f:
        return json.load(f)


def update_cfg(cfg):
    with open('cfg.json', 'w') as f:
        json.dump(cfg, f, indent=2)


def get_links():
    with open('links.json') as f:
        return json.load(f)


def update_links(links):
    with open('links.json', 'w') as f:
        json.dump(links, f, indent=2)


if __name__ == '__main__':
    pass