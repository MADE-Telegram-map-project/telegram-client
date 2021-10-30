from omegaconf import OmegaConf

from core.entities import ClientConfigSchema


if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(ClientConfigSchema)
    config = OmegaConf.merge(schema, base_config)
    config: ClientConfigSchema = OmegaConf.to_object(config)

    print(config)
    print(config.session)
