import os
import json

input_folder = 'dataset/tomato/ann'
output_folder = 'dataset/tomato/labels'

os.makedirs(output_folder, exist_ok=True)

# Từ điển ánh xạ classTitle sang class_id
class_mapping = {}

# Hàm ánh xạ hoặc thêm mới nếu chưa có
def get_class_id(class_title):
    if class_title not in class_mapping:
        class_mapping[class_title] = len(class_mapping)  # Tạo ID mới
    return class_mapping[class_title]

for json_file in os.listdir(input_folder):
    if json_file.endswith('.json'):
        with open(os.path.join(input_folder, json_file), 'r') as f:
            data = json.load(f)

        output_lines = []

        for obj in data['objects']:
            class_title = obj['classTitle']
            class_id = get_class_id(class_title)  # Lấy ID từ class_title

            points = obj['points']['exterior']

            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            xmin, xmax = min(x_coords), max(x_coords)
            ymin, ymax = min(y_coords), max(y_coords)

            x_center = (xmin + xmax) / 2
            y_center = (ymin + ymax) / 2
            width = xmax - xmin
            height = ymax - ymin

            output_line = f"{class_id} {x_center / data['size']['width']:.4f} {y_center / data['size']['height']:.4f} {width / data['size']['width']:.4f} {height / data['size']['height']:.4f}"
            output_lines.append(output_line)

        base_name = os.path.splitext(json_file)[0]
        output_txt_file = f"{base_name}.txt"

        with open(os.path.join(output_folder, output_txt_file), 'w') as f:
            f.write("\n".join(output_lines))

        print(f"Conversion complete for file {json_file} and saved to {output_txt_file}")

# In ra ánh xạ cuối cùng để bạn kiểm tra
print("\nClass Mapping:")
for class_title, class_id in class_mapping.items():
    print(f"{class_title}: {class_id}")
