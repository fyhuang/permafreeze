from permafreeze import PfConfig

def get_test_config():
    cp = PfConfig()
    cp.add_section("options")
    cp.set("options", "site-name", "test")
    cp.set("options", "s3-bucket-name", "test")
    cp.set("options", "glacier-vault-name", "test")
    cp.set("options", "s3-create-bucket", "True")
    cp.set("options", "config-dir", "cfg")
    cp.add_section("targets")
    cp.set("targets", "testfiles", TESTFILES_PATH)

    cp.set("options", "s3-host", "127.0.0.1")
    cp.set("options", "s3-port", "4567")

    cp.add_section("auth")
    cp.set("auth", "accessKeyId", "AKID")
    cp.set("auth", "secretAccessKey", "SAK")

    cp.set_default_options()
    return cp
