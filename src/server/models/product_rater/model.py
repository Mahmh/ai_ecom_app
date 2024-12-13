from typing import List, Optional
import torch, torch.nn as nn
from src.lib.data.models import NeuralNetwork
from src.lib.data.models import ProductRaterInput

class ProductRater(NeuralNetwork):
    def forward(self, input_batch: List[torch.Tensor], targets: Optional[torch.Tensor] = None, training: bool = False) -> torch.Tensor:
        # input_batch = [review_text, rating]; targets = sentiment
        # {review_text} input_batch[0] => (int)   torch.Size([batch_size, seq_len])
        # {rating}     input_batch[1]  => (float) torch.Size([batch_size])
        # {sentiment}   targets        => (int)   torch.Size([batch_size])

        # You should embed before concatenating to make sure the concatenated tensor has a single data type

        if training: self.neural_net.train()
        else: self.neural_net.eval()

        if targets is not None:
            y_pred = self.neural_net(input_batch).squeeze(1)  # torch.Size([batch_size, n_features])
            loss = nn.CrossEntropyLoss()(y_pred, targets)
            return loss
        else:
            return self.neural_net(input_batch)


class Recommender:
    ...