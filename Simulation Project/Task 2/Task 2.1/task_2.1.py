from collections import deque
import pandas as pd
import os

class Simulator:
    def __init__(self, rt_arrival_time, non_rt_arrival_time, rt_service_time, non_rt_service_time, max_mc):
        self.rt_arrival_time = rt_arrival_time
        self.non_rt_arrival_time = non_rt_arrival_time
        self.rt_service_time = rt_service_time
        self.non_rt_service_time = non_rt_service_time
        self.max_mc = max_mc

        self.RT_queue = deque([])
        self.nonRT_queue = deque([])
        self.mc = 0
        self.RTCL = 3
        self.nonRTCL = 5
        self.n_RT = 0
        self.n_non_RT = 0
        self.SCL = 4
        self.preempt_service_time = 0 
        self.s = 2  # 0: idle, 1: serving RT, 2: serving nonRT
        self.event_list = [[self.RTCL, 0], [self.nonRTCL, 1], [self.SCL, 2]]
        self.data = []
        current_data = [self.mc,self.RTCL, self.nonRTCL, self.n_RT, self.n_non_RT, self.SCL, self.s, self.preempt_service_time]
        self.columns = ['MC', 'RTCL', 'nonRTCL','n_RT', 'n_nonRT', 'SCL',  's', 'Pre-empt']
        # self.data.append(current_data)
        self.df = pd.DataFrame(columns = self.columns)


    def start_simulation(self):
        while self.mc <= self.max_mc:
            self.log_state()
            if self.SCL == 0:
                event = min(self.event_list[:2])
            else : 
                event = min(self.event_list)
            # print(event)
            # print(event[1])
            # self.mc = event[0]
            # print(type(self.mc))
            # print(event[1])
            # if event[0] > self.max_mc:
            #     # self.log_state()
            #     # self.write_to_dataframe()
            #     break 
            self.mc = event[0] 
            if event[1] == 0:
                self.handle_RT_arrival()
            elif event[1] == 1:
                self.handle_nonRT_arrival()
            elif event[1] == 2:
                self.handle_service_completion()

            # self.log_state()

        self.write_to_dataframe()

    def handle_RT_arrival(self):
        # print(type(self.RTCL))
        self.mc = self.RTCL
        self.RT_queue.append(self.RTCL)
        self.n_RT += 1
        self.RTCL += rt_arrival_time
        self.event_list[0][0] = self.RTCL

        if self.n_RT == 1 :
            if self.s == 0:
                self.RT_queue.pop()
                self.SCL = self.mc + self.rt_service_time
                self.n_RT -= 1
                self.s = 1
            elif self.s == 2:
                self.RT_queue.pop()
                if (self.SCL - self.mc) != 0 :
                    self.preempt_service_time =  self.SCL - self.mc
                    self.nonRT_queue.append(self.preempt_service_time+self.mc)
                    self.n_non_RT += 1

                elif self.SCL - self.mc == 0:
                    self.preempt_service_time = 0
                
                self.SCL = self.mc + self.rt_service_time
                self.n_RT -= 1
                self.s = 1
            self.event_list[2][0] = self.SCL

    def handle_nonRT_arrival(self):
        self.mc = self.nonRTCL
        self.nonRT_queue.append(self.nonRTCL)
        self.n_non_RT += 1
        self.nonRTCL += non_rt_arrival_time 

        if len(self.nonRT_queue) == 1 and self.s == 0:
            self.nonRT_queue.pop()
            self.SCL = self.mc + self.non_rt_service_time
            self.s = 2
        
        self.n_non_RT -= 1
        self.event_list[1][0] = self.nonRTCL
        self.event_list[2][0] = self.SCL

    def handle_service_completion(self):
        self.mc = self.SCL
        if len(self.RT_queue) > 0:
            self.RT_queue.pop()
            self.SCL = self.mc + self.rt_service_time
            self.s =1
            self.n_RT -= 1

        elif len(self.RT_queue) == 0 and len(self.nonRT_queue) > 0:
            # self.start_service('nonRT')
            self.nonRT_queue.pop()
            if self.preempt_service_time > 0 :
                self.SCL = self.mc + self.preempt_service_time
                self.preempt_service_time = 0
            else:
                self.SCL = self.mc + self.non_rt_service_time
            self.s = 2
            self.n_non_RT -= 1

        else:
            self.s = 0
            self.SCL = 0
        
        self.event_list[2][0] = self.SCL

    def log_state(self):
        # if self.data and self.data[-1][0] != self.mc:
        self.data.append([self.mc, self.RTCL, self.nonRTCL, len(self.RT_queue), len(self.nonRT_queue), self.SCL, self.s, self.preempt_service_time])

    def write_to_dataframe(self):
        self.df = pd.DataFrame(self.data, columns=self.columns)
        print(self.df)

    # def write_to_csv(self, filepath=r'C:\Users\nayan\Documents\IoT Analytics\Projects\Task_2.1_Output.csv'):
    def write_to_csv(self, filepath='Task_2.1_Output.csv'):
        self.df = pd.DataFrame(self.data, columns=self.columns)
        self.df.to_csv(filepath, index=False)
        print(self.df)
        print(f"Data written to {filepath}")
        absolute_path = os.path.abspath(filepath)
        print(f"Data will be written to {absolute_path}")

# Testing 1.1 table
# rt_arrival_time = int(10)
# non_rt_arrival_time = int(5)
# rt_service_time = int(2)
# non_rt_service_time = int(4)
# max_mc = int(50)
        
# Testing 1.2 table
# rt_arrival_time = int(5)
# non_rt_arrival_time = int(10)
# rt_service_time = int(4)
# non_rt_service_time = int(2)
# max_mc = int(20)
        
rt_arrival_time = int(input("Enter the mean inter arrival time of RT messages: "))
non_rt_arrival_time = int(input("Enter the mean inter arrival time of non RT messages: "))
rt_service_time = int(input("Enter the mean service time of RT messages: "))
non_rt_service_time = int(input("Enter the mean service time of non RT messages: "))
max_mc = int(input("Enter the max time till MC should reaach: "))
simulator = Simulator(rt_arrival_time, non_rt_arrival_time, rt_service_time, non_rt_service_time, max_mc)
simulator.start_simulation()
simulator.write_to_csv()
