from omegaconf import OmegaConf

from core.entities import ClientSchema


if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(ClientSchema)
    config = OmegaConf.merge(schema, base_config)
    config: ClientSchema = OmegaConf.to_object(base_config)

    print(config)
