if __name__ == "__main__":

    import sys

    from os.path import abspath, dirname, join

    path = abspath(join(dirname(__file__), ".."))
    sys.path.insert(1, path)

    from jinja2 import Template

    deployment_id, deployment_group, domain, app_name = sys.argv[1:]

    nginx_template_path = f"/home/datamade/{app_name}-{deployment_id}/configs/{deployment_group}.conf.nginx"
    nginx_outpath = f"/etc/nginx/conf.d/{app_name}.conf"
    supervisor_template_path = f"/home/datamade/{app_name}-{deployment_id}/configs/{deployment_group}.conf.supervisor"
    supervisor_outpath = f"/etc/supervisor/conf.d/{app_name}.conf"

    with open(nginx_template_path) as f:
        nginx_conf = Template(f.read())
        context = {
            "deployment_id": deployment_id,
            "domain": domain,
            "app_name": app_name,
        }
        nginx_rendered = nginx_conf.render(context)

    with open(supervisor_template_path) as f:
        supervisor_conf = Template(f.read())
        context = {
            "deployment_id": deployment_id,
            "app_name": app_name,
        }
        supervisor_rendered = supervisor_conf.render(context)

    with open(nginx_outpath, "w") as out:
        out.write(nginx_rendered)

    with open(supervisor_outpath, "w") as out:
        out.write(supervisor_rendered)
