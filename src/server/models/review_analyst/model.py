from typing import List, Union, Optional
import torch, torch.nn as nn
from src.lib.data.models import NeuralNetwork

class ReviewAnalyst(NeuralNetwork):
    """Model class for the Review Analyst. It takes in the review and its rating of a product to output the predicted sentiment of that review."""
    def forward(
            self, 
            input_batch: Union[List[torch.Tensor], List[Union[str, float]]], 
            targets: Optional[torch.Tensor] = None, 
            training: bool = False
        ) -> torch.Tensor:
        """
        The input will be transformed in such a way that can be passed into this neural network:
        - "review_text": `input_batch[0] => (int)   torch.Size([batch_size, seq_len])`
        - "rating":     `input_batch[1] => (float) torch.Size([batch_size])`
        - "sentiment":   `targets        => (int)   torch.Size([batch_size])`

        Output: If sentiment is already inputted as `targets`, the loss is computed & returned. Otherwise, the sentiment is predicted & returned.
        """
    
        if type(input_batch[0]) is str and type(input_batch[1]) is float:
            input_batch, _ = self.config.prep_sample(input_batch[0], input_batch[1], 0)
            input_batch[0], input_batch[1] = input_batch[0].unsqueeze(0), input_batch[1].unsqueeze(0)

        # You should embed before concatenating to make sure the concatenated tensor has a single data type
        embedded = self.embd_table(input_batch[0])                  # (float) torch.Size([batch_size, seq_len, d_model])
        embedded = embedded.reshape(embedded.shape[0], -1)          # torch.Size([batch_size, seq_len*d_model])
        input_batch[1] = input_batch[1].unsqueeze(1)                # torch.Size([batch_size, 1])
        input_batch = torch.cat((embedded, input_batch[1]), dim=1)  # torch.Size([batch_size, (seq_len*d_model)+1])

        if training: self.neural_net.train()
        else: self.neural_net.eval()

        if targets is not None:
            y_pred = self.neural_net(input_batch).squeeze(1)        # torch.Size([batch_size])
            loss = nn.BCELoss()(y_pred, targets)                    # torch.Size([batch_size])
            return loss
        else:
            return self.neural_net(input_batch)                     # torch.Size([batch_size, n_outputs])