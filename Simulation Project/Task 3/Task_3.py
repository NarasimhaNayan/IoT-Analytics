from collections import deque
import pandas as pd
import os
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, rt_arrival_time, non_rt_arrival_time, rt_service_time, non_rt_service_time, batch_size,number_of_batches):
        self.rt_arrival_time = rt_arrival_time
        self.non_rt_arrival_time = non_rt_arrival_time
        self.rt_service_time = rt_service_time
        self.non_rt_service_time = non_rt_service_time
        # self.max_mc = max_mc
        self.batch_size = batch_size
        self.number_of_batches = number_of_batches

        self.RT_queue = deque([])
        self.nonRT_queue = deque([])
        self.RT_response_queue = deque([])
        self.nonRT_response_queue = deque([])
        self.batch_mean_of_RT = []
        self.batch_mean_of_nonRT = []
        self.batch_percentile_of_RT = []
        self.batch_percentile_of_nonRT = []
        self.cur_msg_arrival_time = 0
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
        # current_data = [self.mc,self.RTCL, self.nonRTCL, self.n_RT, self.n_non_RT, self.SCL, self.s, self.preempt_service_time]
        self.columns = ['MC', 'RTCL', 'nonRTCL','n_RT', 'n_nonRT', 'SCL',  's', 'Pre-empt']
        # self.data.append(current_data)
        self.df = pd.DataFrame(columns = self.columns)

    def exp_distributed_random (self,mean) :
        return -1*((mean)*(np.log(np.random.uniform())))


    def start_simulation(self):
        while self.number_of_batches >= len(self.batch_mean_of_RT) or self.number_of_batches >= len(self.batch_mean_of_nonRT) :
            self.log_state()
            if self.SCL == 0:
                event = min(self.event_list[:2])
            else : 
                event = min(self.event_list)
            self.mc = event[0] 
            if event[1] == 0:
                self.handle_RT_arrival()
            elif event[1] == 1:
                self.handle_nonRT_arrival()
            elif event[1] == 2:
                self.handle_service_completion()

        #     self.log_state()

        self.write_to_dataframe()

    def handle_RT_arrival(self):
        # print(type(self.RTCL))
        # self.mc = self.RTCL
        self.RT_queue.append(self.RTCL)
        self.n_RT += 1
        self.RTCL += self.exp_distributed_random(self.rt_arrival_time)
        self.event_list[0][0] = self.RTCL

        if self.n_RT == 1 :
            if self.s == 0:
                self.cur_msg_arrival_time = self.RT_queue.pop()
                self.SCL = self.mc + self.exp_distributed_random(self.rt_service_time)
                self.n_RT -= 1
                self.s = 1
            elif self.s == 2:
                # self.RT_queue.pop()
                if (self.SCL - self.mc) != 0 :
                    self.preempt_service_time =  self.SCL - self.mc
                    self.nonRT_queue.append(self.preempt_service_time+self.mc)
                    self.n_non_RT += 1

                elif self.SCL - self.mc == 0:
                    self.preempt_service_time = 0
                    self.nonRT_response_queue.append(self.mc - self.cur_msg_arrival_time)
                
                self.cur_msg_arrival_time = self.RT_queue.pop()
                self.SCL = self.mc + self.exp_distributed_random(self.rt_service_time)
                self.n_RT -= 1
                self.s = 1
            self.event_list[2][0] = self.SCL

    def handle_nonRT_arrival(self):
        self.mc = self.nonRTCL
        self.nonRT_queue.append(self.nonRTCL)
        self.n_non_RT += 1
        self.nonRTCL += self.exp_distributed_random(self.non_rt_arrival_time) 

        if len(self.nonRT_queue) == 1 and self.s == 0:
            self.cur_msg_arrival_time = self.nonRT_queue.pop()
            self.SCL = self.mc + self.exp_distributed_random(self.non_rt_service_time)
            self.s = 2
        
        self.n_non_RT -= 1
        self.event_list[1][0] = self.nonRTCL
        self.event_list[2][0] = self.SCL

    def handle_service_completion(self):
        if self.s == 1 :
            response_duration = self.mc - self.cur_msg_arrival_time
            self.RT_response_queue.append(response_duration)

            if len(self.RT_response_queue) == self.batch_size:
                # Computing statistics once a batch is complete
                average_response_time_RT = np.mean(self.RT_response_queue)
                percentile_95_response_time_RT = np.percentile(self.RT_response_queue, 95)

                self.batch_mean_of_RT.append(average_response_time_RT)
                self.batch_percentile_of_RT.append(percentile_95_response_time_RT)

                # Clearing the queue for the next batch
                self.RT_response_queue.clear()
        else:
            response_duration = self.mc - self.cur_msg_arrival_time
            self.nonRT_response_queue.append(response_duration)

            if len(self.nonRT_response_queue) == self.batch_size:
                # Computing statistics once a batch is complete
                average_response_time_nonRT = np.mean(self.nonRT_response_queue)
                percentile_95_response_time_nonRT = np.percentile(self.nonRT_response_queue, 95)

                self.batch_mean_of_nonRT.append(average_response_time_nonRT)
                self.batch_percentile_of_nonRT.append(percentile_95_response_time_nonRT)

                # Clearing the queue for the next batch
                self.nonRT_response_queue.clear()
            

        # self.mc = self.SCL
        if len(self.RT_queue) > 0:
            self.cur_msg_arrival_time = self.RT_queue.pop()
            self.SCL = self.mc + self.exp_distributed_random(self.rt_service_time)
            self.s =1
            self.n_RT -= 1

        elif len(self.RT_queue) == 0 and len(self.nonRT_queue) > 0:
            self.cur_msg_arrival_time = self.nonRT_queue.pop()
            if self.preempt_service_time > 0 :
                self.SCL = self.mc + self.preempt_service_time
                self.preempt_service_time = 0
            else:
                self.SCL = self.mc + self.exp_distributed_random(self.non_rt_service_time)
            self.s = 2
            self.n_non_RT -= 1

        else:
            self.s = 0
            self.SCL = 0
        
        self.event_list[2][0] = self.SCL

    def log_state(self):
        # if self.data and self.data[-1][0] != self.mc:
        self.data.append([self.mc, self.RTCL, self.nonRTCL, len(self.RT_queue), len(self.nonRT_queue), self.SCL, self.s, self.preempt_service_time])
        # print('MC:', self.mc, 'RTCL:', self.RTCL, 'nonRTCL:', self.nonRTCL, 'nRT:', len(self.RT_queue), 'non_nRT:', len(self.nonRT_queue),
        #       'SCL:', self.SCL, 's:', self.s, 'pre-empt:', self.preempt_service_time)

    def write_to_dataframe(self):
        self.df = pd.DataFrame(self.data, columns=self.columns)
        # print(self.df)

# Create dataframes for storing batch results
df_RT_mean_batch = pd.DataFrame(columns=['MIAT_nonRT', 'mean', '95th percentile', 'confidence interval', 'error margin'])
df_nonRT_mean_batch = pd.DataFrame(columns=['MIAT_nonRT', 'mean', '95th percentile', 'confidence interval', 'error margin'])
df_RT_percentile_batch = pd.DataFrame(columns=['MIAT_nonRT', 'mean', '95th percentile', 'confidence interval', 'error margin'])
df_nonRT_percentile_batch = pd.DataFrame(columns=['MIAT_nonRT', 'mean', '95th percentile', 'confidence interval', 'error margin'])  


def compute_append_rt_mean_batch(simulation, mean_interarrival_time):
    rt_avg = np.mean(simulation.batch_mean_of_RT)
    rt_95th_percentile = np.percentile(simulation.batch_mean_of_RT, 95)
    rt_conf_interval = stats.t.interval(0.95, df=len(simulation.batch_mean_of_RT)-1, loc=rt_avg, scale=stats.sem(simulation.batch_mean_of_RT))
    rt_error_margin = rt_conf_interval[1] - rt_conf_interval[0]

    return {'MIAT_nonRT': mean_interarrival_time, 'mean': rt_avg, '95th percentile': rt_95th_percentile, 'confidence interval': rt_conf_interval, 'error margin': rt_error_margin}

def compute_append_nonrt_mean_batch(simulation,mean_interarrival_time):
    nonrt_avg = np.mean(simulation.batch_mean_of_nonRT)
    nonrt_95th_percentile = np.percentile(simulation.batch_mean_of_nonRT, 95)
    nonrt_conf_interval = stats.t.interval(0.95, df=len(simulation.batch_mean_of_nonRT)-1, loc=nonrt_avg, scale=stats.sem(simulation.batch_mean_of_nonRT))
    nonrt_error_margin = nonrt_conf_interval[1] - nonrt_conf_interval[0]

    return {'MIAT_nonRT': mean_interarrival_time, 'mean': nonrt_avg, '95th percentile': nonrt_95th_percentile, 'confidence interval': nonrt_conf_interval, 'error margin': nonrt_error_margin}

def compute_append_rt_percentile_batch(simulation, mean_interarrival_time):
    rt_avg = np.mean(simulation.batch_percentile_of_RT)
    rt_95th_percentile = np.percentile(simulation.batch_percentile_of_RT, 95)
    rt_conf_interval = stats.t.interval(0.95, df=len(simulation.batch_percentile_of_RT)-1, loc=rt_avg, scale=stats.sem(simulation.batch_percentile_of_RT))
    rt_error_margin = rt_conf_interval[1] - rt_conf_interval[0]

    return {'MIAT_nonRT': mean_interarrival_time, 'mean': rt_avg, '95th percentile': rt_95th_percentile, 'confidence interval': rt_conf_interval, 'error margin': rt_error_margin}

def compute_append_nonrt_percentile_batch(simulation, mean_interarrival_time):
    nonrt_avg = np.mean(simulation.batch_percentile_of_nonRT)
    nonrt_95th_percentile = np.percentile(simulation.batch_percentile_of_nonRT, 95)
    nonrt_conf_interval = stats.t.interval(0.95, df=len(simulation.batch_percentile_of_nonRT)-1, loc=nonrt_avg, scale=stats.sem(simulation.batch_percentile_of_nonRT))
    nonrt_error_margin = nonrt_conf_interval[1] - nonrt_conf_interval[0]

    return {'MIAT_nonRT': mean_interarrival_time, 'mean': nonrt_avg, '95th percentile': nonrt_95th_percentile, 'confidence interval': nonrt_conf_interval, 'error margin': nonrt_error_margin}




rt_arrival_time = int(input("Enter the mean inter arrival time of RT messages, M_I_AT_RT: "))
rt_service_time = int(input("Enter the mean service time of RT messages, M_ST_RT: "))
non_rt_service_time = int(input("Enter the mean service time of non RT messages, M_ST_nonRT: "))
number_of_batches = int(input("Enter the number of batches, m: "))
batch_size = int(input("Enter the batch size, b: "))
# rt_arrival_time = 7
# rt_service_time = 2
# non_rt_service_time = 4
# number_of_batches = 51
# batch_size =1000
non_rt_arrival_time_sequence = [10,15,20,25,30,35,40]
# max_mc = int(input("Enter the max time till MC should reaach: "))
for nonRT_arrival_time in non_rt_arrival_time_sequence:
    simulator = Simulator(rt_arrival_time, nonRT_arrival_time, rt_service_time, non_rt_service_time, batch_size,number_of_batches)
    simulator.start_simulation()

    simulator.batch_mean_of_RT = simulator.batch_mean_of_RT[1:51]
    simulator.batch_percentile_of_RT = simulator.batch_percentile_of_RT[1:51]
    simulator.batch_mean_of_nonRT = simulator.batch_mean_of_nonRT[1:51]
    simulator.batch_percentile_of_nonRT = simulator.batch_percentile_of_nonRT[1:51]

    # Calculation of batch mean and batch percentile
    new_row_RT_mean_batch = compute_append_rt_mean_batch(simulator, nonRT_arrival_time)
    df_RT_mean_batch = pd.concat([df_RT_mean_batch, pd.DataFrame([new_row_RT_mean_batch])], ignore_index=True)
    new_row_nonRT_mean_batch = compute_append_nonrt_mean_batch(simulator, nonRT_arrival_time)
    df_nonRT_mean_batch = pd.concat([df_nonRT_mean_batch, pd.DataFrame([new_row_nonRT_mean_batch])], ignore_index=True)
    new_row_df_RT_percentile_batch = compute_append_rt_percentile_batch(simulator, nonRT_arrival_time)
    df_RT_percentile_batch = pd.concat([df_RT_percentile_batch, pd.DataFrame([new_row_df_RT_percentile_batch])], ignore_index=True)
    new_row_df_nonRT_percentile_batch = compute_append_nonrt_percentile_batch(simulator, nonRT_arrival_time)
    df_nonRT_percentile_batch = pd.concat([df_nonRT_percentile_batch, pd.DataFrame([new_row_df_nonRT_percentile_batch])], ignore_index=True)

    # Display RT and nonRT message statistics for mean batches
print("RT Message Statistics - Mean Batches:")
print(df_RT_mean_batch)

print("NonRT Message Statistics - Mean Batches:")
print(df_nonRT_mean_batch)

# Set up the plot for Mean Response Time comparison
fig, ax = plt.subplots(figsize=(12, 6))
index_positions = np.arange(len(non_rt_arrival_time_sequence))
bar_width = 0.3
color_rt = 'red'
color_nonrt = 'green'
# Plotting for RT and nonRT messages
bars_rt = ax.bar(index_positions - bar_width/2, df_RT_mean_batch['mean'], bar_width, yerr=df_RT_mean_batch['error margin'],alpha=0.5, ecolor='black', capsize=10, label='RT Messages',color=color_rt)
bars_non_rt = ax.bar(index_positions + bar_width/2, df_nonRT_mean_batch['mean'], bar_width, yerr=df_nonRT_mean_batch['error margin'], alpha=0.5, ecolor='black', capsize=10, label='NonRT Messages',color=color_nonrt)

# Setting labels and titles
ax.set_ylabel('Mean Response Time')
ax.set_xlabel('Mean Inter-Arrival Time of NonRT Messages')
ax.set_title('Comparison of Mean Response Times: RT vs NonRT')
ax.set_xticks(index_positions)
ax.set_xticklabels(non_rt_arrival_time_sequence)
ax.legend()

# Adjust layout and display the plot
fig.tight_layout()
plt.show()

# Display statistics for percentile batches
print("Percentile Batch Statistics - RT Messages:")
print(df_RT_percentile_batch)

print("Percentile Batch Statistics - NonRT Messages:")
print(df_nonRT_percentile_batch)

# Plotting for percentile response time comparison
fig, ax = plt.subplots(figsize=(12, 6))

# Plotting the bars for RT and nonRT message statistics
bars_rt_percentile = ax.bar(index_positions - bar_width/2, df_RT_percentile_batch['mean'], bar_width, yerr=df_RT_percentile_batch['error margin'], alpha=0.5, ecolor='black', capsize=10, label='RT Messages',color=color_rt)
bars_non_rt_percentile = ax.bar(index_positions + bar_width/2, df_nonRT_percentile_batch['mean'], bar_width, yerr=df_nonRT_percentile_batch['error margin'], alpha=0.5, ecolor='black', capsize=10, label='NonRT Messages',color=color_nonrt)

# Configuring plot settings
ax.set_ylabel('95th Percentile Response Time')
ax.set_xlabel('Mean Inter-Arrival Time of NonRT Messages')
ax.set_title('RT vs NonRT: 95th Percentile Response Time Analysis')
ax.set_xticks(index_positions)
ax.set_xticklabels(non_rt_arrival_time_sequence)
ax.legend()

# Final layout adjustment and plot display
fig.tight_layout()
plt.show()

