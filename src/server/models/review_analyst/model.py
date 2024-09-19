import torch, torch.nn as nn

class ReviewAnalyst(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.neural_net = nn.Sequential()

        for i in range(len(config.layers)):
            if i == 0:
                # If the module is the first
                self.neural_net.add_module(f'fc{i+1}', nn.Linear(config.n_inputs, config.layers[i]))
                self.neural_net.add_module(f'relu{i+1}', nn.ReLU())
            elif i != len(config.layers)-1:
                # If the module is not the last
                self.neural_net.add_module(f'fc{i+1}', nn.Linear(config.layers[i-1], config.layers[i]))
                self.neural_net.add_module(f'relu{i+1}', nn.ReLU())
            else:
                # If the module is the last
                self.neural_net.add_module(f'fc{i+1}', nn.Linear(config.layers[i-1], config.layers[i]))
                self.neural_net.add_module(f'sig{i+1}', nn.Sigmoid())

    def forward(self, input_batch: torch.tensor, targets: torch.tensor = None, training: bool = False) -> torch.tensor:
        input_batch = torch.tensor(input_batch).to(self.config.device) if not isinstance(input_batch, torch.Tensor) else input_batch

        if training:
            self.neural_net.train()
        else:
            self.neural_net.eval()

        if targets is not None:
            y_pred = self.neural_net(input_batch).squeeze(1)  # torch.Size([8, 1]) -> torch.Size([8])
            loss = nn.BCELoss()(y_pred, targets)
            return loss
        else:
            return self.neural_net(input_batch)