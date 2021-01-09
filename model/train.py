import pkbar
import torch

def model_loss(model, sentiment, review):
    sentiment = sentiment.type(torch.cuda.LongTensor)           
    review = review.type(torch.cuda.LongTensor)  
    
    # loss is computed by BertForSequenceClassification
    loss, _ = model(review, sentiment)      # discarding pred here

    return loss


def checkpoint(model, valid_loss):
    torch.save(
        {'model_state_dict' : model.state_dict(),
            'valid_loss' : valid_loss},
            './checkpoints/model.pt'
    )

    print("Saved checkpoint... Validation loss reported: {}".format(valid_loss))


def train(model, optimizer, t_loader, v_loader, num_epochs=5):
    step_count = 0
    best_loss = float("Inf")
    train_loss = 0.0
    valid_loss = 0.0

    model.train()
    for epoch in range(num_epochs):
        kbar = pkbar.Kbar(target=len(t_loader), epoch=epoch, num_epochs=num_epochs, width=10, always_stateful=False)

        for p_t, ((review, sentiment), _) in enumerate(t_loader):
            optimizer.zero_grad()       # zero grads 
            loss = model_loss(model, sentiment, review)     # calc loss
            loss.backward()         # update grads
            optimizer.step()        # update parameters

            # record loss and update step count
            train_loss += loss.item()

            # update progress bar
            kbar.update(p_t, values=[("training loss", train_loss)])

            # validation 
            if p_t == len(t_loader):
                model.eval()    # pause training

                with torch.no_grad():
                    for p_v, ((review, sentiment), _) in enumerate(v_loader):
                        loss = model_loss(model, sentiment, review)
                        valid_loss += loss.item()
                        kbar.add(1, values=[('validation loss', valid_loss)])
                
                avg_valid_loss = valid_loss/len(v_loader)

                # reset training/validation loss
                train_loss = 0.0
                valid_loss = 0.0

                if best_loss > avg_valid_loss:
                    best_loss = avg_valid_loss

                    # save checkpoint
                    checkpoint(model, valid_loss)

    checkpoint(model, valid_loss)