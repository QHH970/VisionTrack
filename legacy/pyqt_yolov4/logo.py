import matplotlib.pyplot as plt
import matplotlib.patches as patches


# 创建图形对象
fig, ax = plt.subplots(figsize=(6, 6))

# 背景颜色
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# 绘制一个带有车轮的车辆形状
def draw_car(ax, center, width=0.4, height=0.2):
    # 车身
    car_body = patches.Rectangle((center[0] - width / 2, center[1] - height / 2), width, height, linewidth=2, edgecolor='black', facecolor='blue')
    ax.add_patch(car_body)
    # 车窗
    car_window = patches.Rectangle((center[0] - width / 4, center[1] - height / 8), width / 2, height / 4, linewidth=2, edgecolor='black', facecolor='lightblue')
    ax.add_patch(car_window)
    # 车轮
    wheel_radius = 0.05
    wheel1 = patches.Circle((center[0] - width / 4, center[1] - height / 2), wheel_radius, color='black')
    wheel2 = patches.Circle((center[0] + width / 4, center[1] - height / 2), wheel_radius, color='black')
    ax.add_patch(wheel1)
    ax.add_patch(wheel2)

# 在中心绘制一辆车
draw_car(ax, (0.5, 0.5))

# 绘制道路元素
road_lines = [(0.1, 0.5), (0.3, 0.5), (0.5, 0.5), (0.7, 0.5), (0.9, 0.5)]
for start, end in road_lines:
    ax.plot([start, end], [0.5, 0.5], color='black', linewidth=2, linestyle='--')

# 添加车轮外的传感器图案
sensor_radius = 0.15
sensor_circle = patches.Circle((0.5, 0.5), sensor_radius, edgecolor='green', facecolor='none', linestyle='dotted', linewidth=2)
ax.add_patch(sensor_circle)

# 添加项目名称
plt.text(0.5, 0.2, '智行卫士', horizontalalignment='center', fontsize=20, fontweight='bold', color='darkblue')

# 调整图形
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect('equal')
ax.axis('off')

# 保存图形为文件
file_path = "/mnt/data/smart_traffic_monitoring_system_logo_complex.png"
plt.savefig(file_path)

# 显示图形
plt.show()

file_path


