# /usr/bin/python
from src.MyUtils.CheckAliveBase import CheckAliveBase as CheckAlive


def main():
    infrastructure = "metagenomics"
    hosts = ["host4", "host5", "host6", "host7"]
    REST_SERVICES = [("{0}-rescaler".format(h), h, "8000") for h in hosts]
    checker = CheckAlive()
    checker.set_infrastructure_name(infrastructure)
    checker.set_REST_services(REST_SERVICES)
    checker.report()


if __name__ == "__main__":
    main()
