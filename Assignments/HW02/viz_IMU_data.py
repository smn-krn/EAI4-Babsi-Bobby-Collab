
import pandas as pd
import matplotlib.pyplot as plt

def plot_sensor(df: pd.DataFrame, columns: list[str], sensorname: str) -> None:
    # We create a empty figure and axis for plotting
    fig, ax = plt.subplots(figsize=(12, 6))

    # For each column in the list of columns, we plot the data against the timestamp
    for col in columns:
        # This is the actual plotting command, where we specify the x and y data, the label for the legend, and the line width
        ax.plot(df["timestamp_ms"], df[col], label=col, linewidth=1.0)

    ax.set_xlabel("Timestamp")
    ax.set_ylabel(sensorname)
    
    # The label will be the sensor axis (X, Y or Z)
    ax.legend()

    ax.grid(True, which="major", linestyle="-", linewidth=0.8, alpha=0.7)
    fig.tight_layout()
    
    # If you want to save the figure
    #fig.savefig(f"{sensorname}.png", dpi=300)


# We read the CSV file into a pandas DataFrame
df = pd.read_csv("data.csv")

accel_cols = ["accel_x", "accel_y", "accel_z"]
gyro_cols = ["gyro_x", "gyro_y", "gyro_z"]
mag_cols = ["mag_x", "mag_y", "mag_z"]

plot_sensor(df, accel_cols, "Accelerometer")
plot_sensor(df, gyro_cols, "Gyroskop")
plot_sensor(df, mag_cols, "Magnetometer")

# Otherwise the plots will not be displayed
plt.show()