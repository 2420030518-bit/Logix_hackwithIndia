from ultralytics import YOLO

def train_model():
    model = YOLO('yolov8n.pt')
    try:
        results = model.train(
            data='config.yaml',
            epochs=75,
            imgsz=640,
            batch=8,
            name='aether_vision_final_run'
        )
    except Exception as e:
        print(f"\n--- ERROR DURING TRAINING ---")
        print(f"Error: {e}")
        print("Please check if your dataset folders are correctly populated.")

if __name__ == '__main__':
    train_model()