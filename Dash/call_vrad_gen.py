import numpy as np
import pandas as pd


class G:
    ITERATIONS = 100
    DURATIONS = 6120
    fac_id_df = pd.read_excel("data/FacilityIDLookup.xlsx")
    priv_df = pd.read_excel("data/Privileges.xlsx")
    proc_id_df = pd.read_excel("data/ProcedureIDLookup.xlsx")
    rad_sched_df = pd.read_excel("data/RadiologistSchedules.xlsx")
    restr_df = pd.read_excel("data/Restrictions.xlsx")


def process_data():
    G.rads_list = sorted(G.rad_sched_df["RadiologistID"].unique())
    rads_in_priv = sorted(G.priv_df["RadiologistID"].unique())
    red_priv_df = G.priv_df[G.priv_df["RadiologistID"].isin(G.rads_list)]
    G.radiologist_ids = list(set(rads_in_priv).intersection(set(G.rads_list)))
    G.red_rad_sched_df = G.rad_sched_df[G.rad_sched_df["RadiologistID"].isin(G.radiologist_ids)]
    G.facilities = sorted(red_priv_df["FacilityID"].unique())
    G.procedures_list = sorted(G.proc_id_df["ProcedureID"].unique())
    G.modalities = list(G.proc_id_df.Modality.unique())
    start_time = G.rad_sched_df["Start Time"][0]
    G.rad_sched_df['Relative Start Time'] = (G.rad_sched_df["Start Time"] - start_time)/np.timedelta64(1, 's')/60
    G.rad_sched_df['Relative End Time'] = (G.rad_sched_df["End Time"] - start_time)/np.timedelta64(1, 's')/60
    G.radiologists_by_fac = G.priv_df.groupby("FacilityID")["RadiologistID"].apply(list).reset_index(name='Radiologists').set_index("FacilityID")
    G.facilities_by_rad = G.priv_df.groupby("RadiologistID")["FacilityID"].apply(list).reset_index(name='Facilities').set_index("RadiologistID")


G.target_times = {
    1: 2,
    2: 3,
    3: 5
}

G.specialties = {
    1: '1',
    2: '2',
    3: '3',
    4: '4',
    5: '5'
}

def update_globals(urg_time, non_time):
    G.process_times = {
                        1: urg_time,
                        2: .3*(non_time - urg_time),
                        3: non_time
                    }
    
    

def create_arrival_times(sim_time, arr_rate):
    arrival_times = []
    time = 0
    while time < sim_time:
        time += np.random.exponential(arr_rate)
        arrival_times.append(time)
    return arrival_times

def create_medical_images(arrival_times):
    med_images = []
    for i, t in enumerate(arrival_times):
        med_images.append(MedicalImage(i, t, random.sample(list(G.target_times.keys()), 1)[0], random.sample(list(G.specialties.keys()), 1)[0]))
    return med_images

def create_radiologists(num_rads):
    radiologists = []
    for i in range(5):
        specialties_temp = random.sample(list(G.specialties.keys()), random.randrange(2,num_rads))
        radiologists.append(Radiologist(i, specialties_temp))
    return radiologists



def create_initial_events(med_images):
    events=[]
    for img in med_images:
        events.append([img.time_created, 'New Job', img])
    return events


def start_simulation(events, med_images, radiologists):
    s = SystemState(events, med_images, radiologists)
    s.run_simulation()


class MedicalImage(object):    
    def __init__(self, img_id, time_created, urgency, image_type):#, modality, speciality, urgency, image_label):
        self.img_id = img_id
        self.time_created = time_created
        self.urgency = urgency
        self.image_type = image_type
        self.target_time = G.target_times[urgency]
        self.time_remaining = G.target_times[urgency]
        self.est_process_time = G.process_times[urgency]
        self.in_queues = []   #keep track on which queues image is in [rad_id, position]
        self.time_seen = 0
        self.time_done = 0
        self.rad_seen = "None"
        
    def update_time_remaining(self, t):
        self.time_remaining = self.target_time - (t - self.time_created)
        
        
class Radiologist:
    def __init__(self, rad_id, specialties, working=True):
        self.queue = []
        self.queue_data = []#[med_image, image_id, image_urgency, time_left, est_time]
        self.rad_id = rad_id
        self.specialties = specialties
        self.is_working = working
        self.images_served = []
        self.idle_times = []
        self.time_of_last_idle = 0
        self.time_last_not_idle = 0
        self.busy_times = []
        self.time = 0
        self.time_current_job_start = 0
        self.time_of_step = 0
        self.queue_length = []
        self.service_starts = []
        self.service_ends = []
        self.service_time = []  
        
    def get_stats(self):
        return self.idle_times, self.busy_times, self.queue_length, self.service_starts, self.service_ends, self.service_time 
        
    def show_queue(self):
        return self.queue
    
    def add_job(self, med_image, time):
        self.queue.append(med_image)    #each customer is represented by the time it will take for them to be served
        self.queue_data.append([med_image, med_image.img_id, med_image.urgency, med_image.time_remaining, med_image.est_process_time, med_image.est_process_time]) #[image_id, image_urgency, time_left, est_time]
        #print(self.show_queue())
        
    def update_queue(self, time):
        for img in self.queue:
            img.update_time_remaining(time)
        #sort_queue()        
    #def sort_queue(self):
                   
        
        
class SystemState:
    def __init__(self, events, images, rads):
        self.time = 0
        self.events = events
        self.images = images
        self.rads = rads
        self.rads_working = rads
        self.rads_not_working = []
        self.events_history = []
        self.queue_lengths = []
        self.time_steps = []
        self.img_table = pd.DataFrame(columns=['create_time','seen_time', 'finished', 'time_w_rad', 'total_time'])
        self.rad_table = pd.DataFrame()
        
    def create_event(self, time, event_type, obj):
        self.events.append([time, event_type, obj])
        self.events = sorted(self.events, key=lambda x: x[0])

    def update_img_table(self, med_img):
        column_names = ['create_time','seen_time', 'finished', 'time_w_rad', 'total_time']
        values = [med_img.time_created, med_img.time_seen, self.time, self.time - med_img.time_seen, self.time - med_img.time_created]
        self.img_table.append(pd.DataFrame().T, ignore_index = True)
    
        
    def process_event(self):
        event = self.events[0]
        self.events_history.append(event)
        self.time = event[0]       
        event_type = event[1]
        del self.events[0]
        temp_list = []
        for r in self.rads:
            temp_list.append(len(r.queue))
        self.queue_lengths.append(temp_list)
        self.time_steps.append(self.time)
            
        if event_type == "New Job":
            self.distribute_job(event[2])
        elif event_type == "Job Done":
            rad = event[2]
            self.complete_job(rad)
        print("Event processed")
        if len(self.events) > 0:
            self.process_event()
        else:
            print("Simulation complete")
                
    def distribute_job(self, med_image):
        image_type = med_image.image_type
        capable_rads = []
        for rad in self.rads_working:      #finds radiologists capable of working on image
            if image_type in rad.specialties:
                capable_rads.append(rad)
        for rad in capable_rads:
            rad.add_job(med_image, self.time)
            med_image.in_queues.append(rad)    #keep track of which rads have image in queue
            if len(rad.queue)==1:
                self.start_job(rad)
                break         
        self.update_queues()
             
    def update_queues(self):
        for rad in self.rads_working:
            rad.update_queue(self.time)
                
    def start_job(self, rad):
        med_image = rad.queue[0]
        image_type = med_image.image_type
        urgency = med_image.urgency
        rad.service_starts = self.time
        med_image.time_seen = self.time
        med_image.rad_seen = rad.rad_id
        self.events_history.append([self.time, "Job Started", med_image])
        process_time = np.random.exponential(G.target_times[urgency])
        self.create_event(self.time+process_time, "Job Done", rad)
        print(f"Image {med_image.img_id} is seen by radiologist {rad.rad_id} at {self.time}")
        for r in med_image.in_queues:
            if r != rad:
                r.queue.remove(med_image)           
        
    def complete_job(self, rad):
        med_image = rad.queue[0]
        self.update_img_table(med_image)
        rad.images_served.append(med_image.img_id)
        rad.service_ends.append(self.time)
        med_image.time_done = self.time
        print(f"Image {med_image.img_id} is done by radiologist {rad.rad_id} at {self.time}")
        del rad.queue[0]
        if len(rad.queue) > 0:
            self.start_job(rad)

    def run_simulation(self):
        self.process_event()
        
             






