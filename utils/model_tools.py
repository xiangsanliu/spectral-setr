import time
import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from torch.utils.data import DataLoader
from utils.metrics import runningScore


class ModelValidator:
    def __init__(self, config, loss_func):
        self.best_iou = 0
        self.best_score = {}
        self.config = config
        self.loss_func = loss_func
        self.running_metrics_val = runningScore(config["n_classes"])
        pass

    def validate_model(self, model, val_loader, device):
        model.eval()
        n = 0
        val_loss_sum = 0.0
        with torch.no_grad():
            for val_img, val_mask in tqdm(
                val_loader, total=len(val_loader), desc="Valid", unit=" step"
            ):
                n += 1
                val_img = val_img.to(device)
                val_mask = val_mask.to(device)
                pred_img = model(val_img)
                val_loss = self.loss_func(pred_img, val_mask)
                pred = pred_img.data.max(1)[1].cpu().numpy()
                gt = val_mask.data.cpu().numpy()
                self.running_metrics_val.update(gt, pred)
                val_loss_sum += val_loss.item()
            score, class_iou, mean_iu = self.running_metrics_val.get_scores()
            print("Valid loss:\t", val_loss_sum / n)
            for k, v in score.items():
                print(k, v)

            if self.config["mode"] == "train":
                self.running_metrics_val.reset()
                if mean_iu > self.best_iou:
                    self.best_score = score
                    self.best_iou = mean_iu
                    print("Saving Best Model...")
                    torch.save(model.state_dict(), self.config["model_save_path"])
                model.train()
        return self.best_score

    def predict(self, model, test_loader):
        with torch.no_grad():
            for img, mask in test_loader:
                print(img.shape)
                pred = model(img)
                pred = pred.data.max(1)[1].cpu().numpy()
                plt.subplot(1, 3, 1)
                img = img.permute(0, 2, 3, 1)
                img = img[0]
                plt.imshow(img[:, :, [80, 60, 35]])
                plt.subplot(1, 3, 2)
                plt.imshow(pred[0], cmap="PuBuGn")
                plt.subplot(1, 3, 3)
                plt.imshow(mask[0], cmap="PuBuGn")
                plt.savefig("./work/predict.jpg")
                plt.show()
                time.sleep(2)

    def draw_predict(self, model, img_data):
        with torch.no_grad():
            pred = model(img_data)
            pred = pred.data.max(1)[1].cpu().numpy()
            return pred
