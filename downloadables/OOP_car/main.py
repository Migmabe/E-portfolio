from onboardcomp import BoardComputer

from csv import reader

#######################################################
date_time = 19  # 19 represents 19:00 hours or 7PM
light_threshold = 4
latest_OV = 1.1
"""Here's the data that would supposedly come from sensors in real time"""
input_data = []
with open("x_y.csv") as g:
    csv_read = reader(g, delimiter=",")
    next(g)  # skip first titles row
    for t, a, orientation, latitude, longitude, obstacle, speed in csv_read:
        input_data.append([t, a, orientation, latitude, longitude, obstacle, speed])

#######################################################

if __name__ == "__main__":
    car1 = BoardComputer()
    car1.run_mode(input_data, latest_OV, light_threshold)
