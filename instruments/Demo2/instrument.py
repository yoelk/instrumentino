    # Add controllers
    simulation_controller = SimulatedController()
    app.add_controller(simulation_controller)

    # Add channels
    flow1_channel_in_out = DataChannelInOutAnalog(controller=simulation_controller, sampling_rate=10)
    enable1_channel_in_out = DataChannelInOutDigital(controller=simulation_controller)
 
    flow2_channel_in_out = DataChannelInOutAnalog(controller=simulation_controller, sampling_rate=10)
    enable2_channel_in_out = DataChannelInOutDigital(controller=simulation_controller)
 
    flow3_channel_in_out = DataChannelInOutAnalog(controller=simulation_controller, sampling_rate=1)
    enable3_channel_in_out = DataChannelInOutDigital(controller=simulation_controller)
 
    # Add components
    app.add_component(MassFlowController(name='MFC1', 
                                         flow_ch_in=flow1_channel_in_out, flow_ch_out=flow1_channel_in_out,
                                         enable_ch_in=enable1_channel_in_out, enable_ch_out=enable1_channel_in_out,))
#     app.add_component(MassFlowController(name='MFC2', 
#                                          flow_ch_in=flow2_channel_in_out, flow_ch_out=flow2_channel_in_out,
#                                          enable_ch_in=enable2_channel_in_out, enable_ch_out=enable2_channel_in_out,))
#     app.add_component(MassFlowController(name='MFC3', 
#                                          flow_ch_in=flow3_channel_in_out, flow_ch_out=flow3_channel_in_out,
#                                          enable_ch_in=enable3_channel_in_out, enable_ch_out=enable3_channel_in_out,))
    
    # Add actions
    app.add_action(name='action1', function=lambda:1)
