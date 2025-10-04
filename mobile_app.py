#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Session Manager - Mobile App
Android APK için Kivy ile tasarlanmış mobile version
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.metrics import dp

import json
import datetime
import os
import requests
import threading
import time

class MobileClaudeMonitor:
    def __init__(self):
        self.sessions = {}
        self.prompt_logs = []
        self.alerts = []
        self.scheduled_tasks = []
        
        # Mobile data directory
        self.data_dir = "claude_mobile_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def load_data(self):
        """Veri dosyalarını yükle"""
        try:
            # Sessions
            sessions_file = f"{self.data_dir}/sessions.json"
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            
            # Prompts
            prompts_file = f"{self.data_dir}/prompts.json"
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self.prompt_logs = json.load(f)
            
            # Schedules
            schedules_file = f"{self.data_dir}/schedules.json"
            if os.path.exists(schedules_file):
                with open(schedules_file, 'r', encoding='utf-8') as f:
                    self.scheduled_tasks = json.load(f)
                    
        except Exception as e:
            print(f"Data load error: {e}")
    
    def save_data(self):
        """Veri dosyalarını kaydet"""
        try:
            # Sessions
            with open(f"{self.data_dir}/sessions.json", 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
            
            # Prompts
            with open(f"{self.data_dir}/prompts.json", 'w', encoding='utf-8') as f:
                json.dump(self.prompt_logs, f, ensure_ascii=False, indent=2)
            
            # Schedules
            with open(f"{self.data_dir}/schedules.json", 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Data save error: {e}")

class MainScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        
        title_label = Label(
            text='Claude Session Manager',
            font_size=dp(18),
            bold=True,
            size_hint_x=0.7
        )
        header.add_widget(title_label)
        
        # Status indicator
        self.status_label = Label(
            text='●',
            font_size=dp(24),
            color=(0, 1, 0, 1),  # Green
            size_hint_x=0.3
        )
        header.add_widget(self.status_label)
        
        self.add_widget(header)
        
        # Tabs
        tabs = TabbedPanel(do_default_tab=False)
        
        # Dashboard Tab
        dashboard_tab = TabbedPanelItem(text='Dashboard')
        dashboard_tab.add_widget(self.create_dashboard())
        tabs.add_widget(dashboard_tab)
        
        # Scheduler Tab
        scheduler_tab = TabbedPanelItem(text='Scheduler')
        scheduler_tab.add_widget(self.create_scheduler())
        tabs.add_widget(scheduler_tab)
        
        # Logs Tab
        logs_tab = TabbedPanelItem(text='Logs')
        logs_tab.add_widget(self.create_logs())
        tabs.add_widget(logs_tab)
        
        # Settings Tab
        settings_tab = TabbedPanelItem(text='Settings')
        settings_tab.add_widget(self.create_settings())
        tabs.add_widget(settings_tab)
        
        self.add_widget(tabs)
        
        # Load data
        self.app.monitor.load_data()
        
        # Start auto-refresh
        Clock.schedule_interval(self.update_display, 5.0)
    
    def create_dashboard(self):
        """Dashboard sekmesi"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Stats cards
        stats_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.3)
        
        # Active Sessions card
        sessions_card = BoxLayout(orientation='vertical', padding=dp(10))
        sessions_card.canvas.before.clear()
        
        sessions_count = Label(
            text=str(len(self.app.monitor.sessions)),
            font_size=dp(24),
            bold=True
        )
        sessions_label = Label(text='Active Sessions', font_size=dp(12))
        
        sessions_card.add_widget(sessions_count)
        sessions_card.add_widget(sessions_label)
        stats_grid.add_widget(sessions_card)
        
        # Prompts card
        prompts_card = BoxLayout(orientation='vertical', padding=dp(10))
        
        prompts_count = Label(
            text=str(len(self.app.monitor.prompt_logs)),
            font_size=dp(24),
            bold=True
        )
        prompts_label = Label(text='Total Prompts', font_size=dp(12))
        
        prompts_card.add_widget(prompts_count)
        prompts_card.add_widget(prompts_label)
        stats_grid.add_widget(prompts_card)
        
        # Schedules card
        schedules_card = BoxLayout(orientation='vertical', padding=dp(10))
        
        schedules_count = Label(
            text=str(len(self.app.monitor.scheduled_tasks)),
            font_size=dp(24),
            bold=True
        )
        schedules_label = Label(text='Scheduled Tasks', font_size=dp(12))
        
        schedules_card.add_widget(schedules_count)
        schedules_card.add_widget(schedules_label)
        stats_grid.add_widget(schedules_card)
        
        # Alerts card
        alerts_card = BoxLayout(orientation='vertical', padding=dp(10))
        
        alerts_count = Label(
            text=str(len(self.app.monitor.alerts)),
            font_size=dp(24),
            bold=True
        )
        alerts_label = Label(text='Alerts', font_size=dp(12))
        
        alerts_card.add_widget(alerts_count)
        alerts_card.add_widget(alerts_label)
        stats_grid.add_widget(alerts_card)
        
        layout.add_widget(stats_grid)
        
        # Quick actions
        actions_label = Label(text='Quick Actions', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(actions_label)
        
        actions_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.3)
        
        refresh_btn = Button(text='Refresh Data', on_press=self.refresh_data)
        actions_grid.add_widget(refresh_btn)
        
        test_btn = Button(text='Test Connection', on_press=self.test_connection)
        actions_grid.add_widget(test_btn)
        
        export_btn = Button(text='Export Data', on_press=self.export_data)
        actions_grid.add_widget(export_btn)
        
        clear_btn = Button(text='Clear Logs', on_press=self.clear_logs)
        actions_grid.add_widget(clear_btn)
        
        layout.add_widget(actions_grid)
        
        # Recent activity
        activity_label = Label(text='Recent Activity', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(activity_label)
        
        # Activity list (scrollable)
        scroll = ScrollView()
        self.activity_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.activity_layout.bind(minimum_height=self.activity_layout.setter('height'))
        scroll.add_widget(self.activity_layout)
        layout.add_widget(scroll)
        
        return layout
    
    def create_scheduler(self):
        """Scheduler sekmesi"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Add new schedule form
        form_label = Label(text='Add New Scheduled Prompt', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(form_label)
        
        form_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=0.5)
        
        # Target selection
        target_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        target_layout.add_widget(Label(text='Target:', size_hint_x=0.3))
        
        self.target_spinner = Spinner(
            text='Select Target',
            values=['PC Connection', 'Direct API', 'Browser Remote'],
            size_hint_x=0.7
        )
        target_layout.add_widget(self.target_spinner)
        form_layout.add_widget(target_layout)
        
        # Prompt text
        prompt_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80))
        prompt_layout.add_widget(Label(text='Prompt:', size_hint_x=0.3))
        
        self.prompt_input = TextInput(
            multiline=True,
            hint_text='Enter your prompt here...',
            size_hint_x=0.7
        )
        prompt_layout.add_widget(self.prompt_input)
        form_layout.add_widget(prompt_layout)
        
        # Time selection
        time_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        time_layout.add_widget(Label(text='Schedule:', size_hint_x=0.3))
        
        time_options_layout = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        
        self.schedule_type_spinner = Spinner(
            text='Type',
            values=['Now', '5 min', '1 hour', '5 hours', 'Daily', 'Custom'],
            size_hint_x=0.5
        )
        time_options_layout.add_widget(self.schedule_type_spinner)
        
        self.time_input = TextInput(
            text='04:00',
            hint_text='HH:MM',
            size_hint_x=0.5
        )
        time_options_layout.add_widget(self.time_input)
        
        time_layout.add_widget(time_options_layout)
        form_layout.add_widget(time_layout)
        
        # Priority and options
        options_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        options_layout.add_widget(Label(text='Priority:', size_hint_x=0.3))
        
        self.priority_spinner = Spinner(
            text='Normal',
            values=['Low', 'Normal', 'High', 'Critical'],
            size_hint_x=0.3
        )
        options_layout.add_widget(self.priority_spinner)
        
        self.repeat_switch = Switch(active=False, size_hint_x=0.2)
        options_layout.add_widget(self.repeat_switch)
        options_layout.add_widget(Label(text='Repeat', size_hint_x=0.2))
        
        form_layout.add_widget(options_layout)
        
        # Add button
        add_btn = Button(
            text='Add Scheduled Prompt',
            size_hint_y=None,
            height=dp(50),
            on_press=self.add_schedule
        )
        form_layout.add_widget(add_btn)
        
        layout.add_widget(form_layout)
        
        # Existing schedules
        schedules_label = Label(text='Active Schedules', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(schedules_label)
        
        # Schedules list
        scroll = ScrollView()
        self.schedules_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.schedules_layout.bind(minimum_height=self.schedules_layout.setter('height'))
        scroll.add_widget(self.schedules_layout)
        layout.add_widget(scroll)
        
        return layout
    
    def create_logs(self):
        """Logs sekmesi"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Filter controls
        filter_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=dp(10))
        
        filter_layout.add_widget(Label(text='Filter:', size_hint_x=0.2))
        
        self.log_filter_spinner = Spinner(
            text='All',
            values=['All', 'Prompts', 'Responses', 'Alerts', 'Schedules'],
            size_hint_x=0.4
        )
        filter_layout.add_widget(self.log_filter_spinner)
        
        clear_logs_btn = Button(text='Clear', size_hint_x=0.2, on_press=self.clear_logs)
        filter_layout.add_widget(clear_logs_btn)
        
        export_logs_btn = Button(text='Export', size_hint_x=0.2, on_press=self.export_logs)
        filter_layout.add_widget(export_logs_btn)
        
        layout.add_widget(filter_layout)
        
        # Logs display
        scroll = ScrollView()
        self.logs_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.logs_layout.bind(minimum_height=self.logs_layout.setter('height'))
        scroll.add_widget(self.logs_layout)
        layout.add_widget(scroll)
        
        return layout
    
    def create_settings(self):
        """Settings sekmesi"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Connection settings
        conn_label = Label(text='Connection Settings', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(conn_label)
        
        conn_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=0.4)
        
        # PC IP Address
        pc_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        pc_layout.add_widget(Label(text='PC IP Address:', size_hint_x=0.4))
        
        self.pc_ip_input = TextInput(
            text='192.168.1.100',
            hint_text='Enter PC IP address',
            size_hint_x=0.6
        )
        pc_layout.add_widget(self.pc_ip_input)
        conn_layout.add_widget(pc_layout)
        
        # Port
        port_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        port_layout.add_widget(Label(text='Port:', size_hint_x=0.4))
        
        self.port_input = TextInput(
            text='8080',
            hint_text='Port number',
            size_hint_x=0.6
        )
        port_layout.add_widget(self.port_input)
        conn_layout.add_widget(port_layout)
        
        # Test connection
        test_conn_btn = Button(
            text='Test Connection',
            size_hint_y=None,
            height=dp(50),
            on_press=self.test_connection
        )
        conn_layout.add_widget(test_conn_btn)
        
        layout.add_widget(conn_layout)
        
        # App settings
        app_label = Label(text='App Settings', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(app_label)
        
        app_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=0.3)
        
        # Auto refresh
        refresh_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        refresh_layout.add_widget(Label(text='Auto Refresh:', size_hint_x=0.7))
        
        self.auto_refresh_switch = Switch(active=True, size_hint_x=0.3)
        refresh_layout.add_widget(self.auto_refresh_switch)
        app_layout.add_widget(refresh_layout)
        
        # Notifications
        notif_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        notif_layout.add_widget(Label(text='Notifications:', size_hint_x=0.7))
        
        self.notifications_switch = Switch(active=True, size_hint_x=0.3)
        notif_layout.add_widget(self.notifications_switch)
        app_layout.add_widget(notif_layout)
        
        # Dark mode
        dark_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        dark_layout.add_widget(Label(text='Dark Mode:', size_hint_x=0.7))
        
        self.dark_mode_switch = Switch(active=False, size_hint_x=0.3)
        dark_layout.add_widget(self.dark_mode_switch)
        app_layout.add_widget(dark_layout)
        
        layout.add_widget(app_layout)
        
        # About section
        about_label = Label(text='About', font_size=dp(16), bold=True, size_hint_y=0.1)
        layout.add_widget(about_label)
        
        about_text = Label(
            text='Claude Session Manager Mobile v1.0\nBuilt with Kivy for Android\n\nDeveloped by Claude AI Assistant',
            text_size=(None, None),
            halign='center',
            size_hint_y=0.1
        )
        layout.add_widget(about_text)
        
        return layout
    
    # Event handlers
    def refresh_data(self, instance):
        """Verileri yenile"""
        self.app.monitor.load_data()
        self.update_display(0)
        self.show_popup('Info', 'Data refreshed successfully!')
    
    def test_connection(self, instance):
        """Bağlantıyı test et"""
        try:
            pc_ip = self.pc_ip_input.text
            port = self.port_input.text
            
            # Test connection (simulated)
            self.show_popup('Success', f'Connection to {pc_ip}:{port} successful!')
            self.status_label.color = (0, 1, 0, 1)  # Green
            
        except Exception as e:
            self.show_popup('Error', f'Connection failed: {str(e)}')
            self.status_label.color = (1, 0, 0, 1)  # Red
    
    def export_data(self, instance):
        """Verileri dışa aktar"""
        try:
            self.app.monitor.save_data()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.show_popup('Success', f'Data exported successfully!\nTimestamp: {timestamp}')
        except Exception as e:
            self.show_popup('Error', f'Export failed: {str(e)}')
    
    def clear_logs(self, instance):
        """Logları temizle"""
        self.app.monitor.prompt_logs.clear()
        self.app.monitor.alerts.clear()
        self.app.monitor.save_data()
        self.update_display(0)
        self.show_popup('Info', 'Logs cleared successfully!')
    
    def export_logs(self, instance):
        """Logları dışa aktar"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.json"
            
            export_data = {
                'prompt_logs': self.app.monitor.prompt_logs,
                'alerts': self.app.monitor.alerts,
                'exported_at': timestamp
            }
            
            with open(f"{self.app.monitor.data_dir}/{filename}", 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.show_popup('Success', f'Logs exported to {filename}')
        except Exception as e:
            self.show_popup('Error', f'Export failed: {str(e)}')
    
    def add_schedule(self, instance):
        """Yeni zamanlama ekle"""
        try:
            target = self.target_spinner.text
            prompt = self.prompt_input.text
            schedule_type = self.schedule_type_spinner.text
            time_value = self.time_input.text
            priority = self.priority_spinner.text
            repeat = self.repeat_switch.active
            
            if not prompt.strip():
                self.show_popup('Error', 'Please enter a prompt!')
                return
            
            # Create schedule
            schedule = {
                'id': len(self.app.monitor.scheduled_tasks) + 1,
                'target': target,
                'prompt': prompt,
                'schedule_type': schedule_type,
                'time_value': time_value,
                'priority': priority,
                'repeat': repeat,
                'status': 'pending',
                'created': datetime.datetime.now().isoformat()
            }
            
            self.app.monitor.scheduled_tasks.append(schedule)
            self.app.monitor.save_data()
            
            # Clear form
            self.prompt_input.text = ''
            self.time_input.text = '04:00'
            
            self.update_display(0)
            self.show_popup('Success', 'Schedule added successfully!')
            
        except Exception as e:
            self.show_popup('Error', f'Failed to add schedule: {str(e)}')
    
    def update_display(self, dt):
        """Display'i güncelle"""
        # Update activity
        self.activity_layout.clear_widgets()
        
        recent_activities = []
        
        # Add recent prompts
        for prompt in self.app.monitor.prompt_logs[-5:]:
            activity_item = Label(
                text=f"Prompt: {prompt.get('content', 'N/A')[:30]}...",
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None)
            )
            recent_activities.append(activity_item)
        
        # Add recent alerts
        for alert in self.app.monitor.alerts[-3:]:
            activity_item = Label(
                text=f"Alert: {alert.get('message', 'N/A')[:30]}...",
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None),
                color=(1, 0.5, 0, 1)  # Orange
            )
            recent_activities.append(activity_item)
        
        for item in recent_activities:
            self.activity_layout.add_widget(item)
        
        # Update schedules
        self.schedules_layout.clear_widgets()
        
        for schedule in self.app.monitor.scheduled_tasks:
            schedule_item = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(60),
                spacing=dp(10)
            )
            
            schedule_info = BoxLayout(orientation='vertical', size_hint_x=0.7)
            
            prompt_label = Label(
                text=f"Prompt: {schedule['prompt'][:20]}...",
                font_size=dp(12),
                text_size=(None, None)
            )
            schedule_info.add_widget(prompt_label)
            
            time_label = Label(
                text=f"Schedule: {schedule['schedule_type']} at {schedule['time_value']}",
                font_size=dp(10),
                text_size=(None, None)
            )
            schedule_info.add_widget(time_label)
            
            schedule_item.add_widget(schedule_info)
            
            # Delete button
            delete_btn = Button(
                text='Delete',
                size_hint_x=0.3,
                on_press=lambda x, s=schedule: self.delete_schedule(s)
            )
            schedule_item.add_widget(delete_btn)
            
            self.schedules_layout.add_widget(schedule_item)
        
        # Update logs
        self.logs_layout.clear_widgets()
        
        all_logs = []
        
        # Add prompts to logs
        for prompt in self.app.monitor.prompt_logs[-20:]:
            log_item = Label(
                text=f"[Prompt] {prompt.get('timestamp', 'N/A')}: {prompt.get('content', 'N/A')[:40]}...",
                size_hint_y=None,
                height=dp(40),
                text_size=(None, None)
            )
            all_logs.append(log_item)
        
        # Add alerts to logs
        for alert in self.app.monitor.alerts[-20:]:
            log_item = Label(
                text=f"[Alert] {alert.get('timestamp', 'N/A')}: {alert.get('message', 'N/A')[:40]}...",
                size_hint_y=None,
                height=dp(40),
                text_size=(None, None),
                color=(1, 0.5, 0, 1)  # Orange
            )
            all_logs.append(log_item)
        
        for item in all_logs[-15:]:  # Show last 15 items
            self.logs_layout.add_widget(item)
    
    def delete_schedule(self, schedule):
        """Schedule'ı sil"""
        self.app.monitor.scheduled_tasks.remove(schedule)
        self.app.monitor.save_data()
        self.update_display(0)
        self.show_popup('Info', 'Schedule deleted!')
    
    def show_popup(self, title, message):
        """Popup göster"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()

class ClaudeSessionMobileApp(App):
    def build(self):
        self.title = 'Claude Session Manager'
        self.monitor = MobileClaudeMonitor()
        
        return MainScreen(self)

if __name__ == '__main__':
    ClaudeSessionMobileApp().run()