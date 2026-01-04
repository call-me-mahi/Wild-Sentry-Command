import time
#alert triggering logic
class AlertController:

    def __init__(self):
        self.counter = 0             
        self.last_alert_time = 0     
        self.limit_frames = 15
        self.limit_time = 10  # 10 seconds

    def check_alert(self, is_detected):
        if is_detected:
            self.counter += 1
        else:
            self.counter = 0
            return False
        
        if self.counter >= self.limit_frames:
            current_time = time.time()
            time_passed = current_time - self.last_alert_time
            
            if time_passed > self.limit_time:
                self.last_alert_time = current_time  # Reset timer
                self.counter = 0 # reset counter
                return True
        
        return False
# --- TESTING SECTION ---
if __name__ == "__main__":
    print("STARTING LOGIC TEST...")
    
    # 1. Create the controller
    brain = AlertController()
    
    # 2. Simulate "Seeing an animal" for 20 frames
    print("\n--- Test 1: Continuous Detection ---")
    for i in range(1, 21):
        result = brain.check_alert(is_detected=True)
        print(f"Frame {i}: Alert? {result}")
        
        # We expect it to say "True" ONLY at Frame 15
        
    # 3. Simulate "Cooldown" 
    print("\n--- Test 2: Cooldown Check ---")
    result = brain.check_alert(is_detected=True)
    print(f"Frame 21 (Immediate): Alert? {result}") # Should be False (Cooldown active)
    
    # 4. Simulate Waiting 
    print("\n--- Test 3: Time Jump (11s later) ---")
    time.sleep(11) # Wait...
    result = brain.check_alert(is_detected=True)
    print("Done.")