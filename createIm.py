import os
from PIL import Image, ImageDraw, ImageFont

# 配置列表：(文件名, 宽, 高, 主色调, 形状/备注)
assets_config = [
    # 角色
        ("player.png", 28, 28, (0, 255, 0, 255), "Player"),
	    ("player_hurt.png", 28, 28, (255, 0, 0, 255), "Hurt"),
	        
		    # 敌人 (使用红色系区分)
		        ("enemy_minion.png", 32, 32, (200, 50, 50, 255), "Minion"),
			    ("enemy_elite.png", 38, 38, (150, 0, 0, 255), "Elite"),
			        ("enemy_boss.png", 48, 48, (100, 0, 0, 255), "BOSS"),
				    
				        # 武器
					    ("bullet.png", 8, 8, (255, 255, 0, 255), "."),
					        
						    # 房间图标 (使用不同颜色区分功能)
						        ("room_start.png", 50, 50, (100, 255, 100, 255), "Start"),
							    ("room_combat.png", 50, 50, (200, 50, 50, 255), "Fight"),
							        ("room_elite.png", 50, 50, (150, 0, 150, 255), "Elite"),
								    ("room_shop.png", 50, 50, (255, 215, 0, 255), "Shop"),
								        ("room_reward.png", 50, 50, (0, 200, 255, 255), "Gift"),
									    ("room_boss.png", 50, 50, (50, 0, 0, 255), "Skull"),
									        
										    # UI元素
										        ("button_normal.png", 100, 40, (100, 100, 100, 255), "Button"),
											    ("button_hover.png", 100, 40, (150, 150, 150, 255), "Hover"),
											        ("button_pressed.png", 100, 40, (50, 50, 50, 255), "Press"),
												    
												        # 卡片背景 (按稀有度配色)
													    ("card_common.png", 280, 120, (180, 180, 180, 255), "Common"),
													        ("card_uncommon.png", 280, 120, (50, 200, 50, 255), "Uncommon"),
														    ("card_rare.png", 280, 120, (50, 50, 200, 255), "Rare"),
														        ("card_epic.png", 280, 120, (180, 50, 200, 255), "Epic"),
															    ("card_legendary.png", 280, 120, (255, 165, 0, 255), "Legend"),
															        
																    # 工坊设施
																        ("facility_forge.png", 40, 40, (255, 100, 50, 255), "Forge"),
																	    ("facility_alchemy.png", 40, 40, (50, 255, 100, 255), "Alch"),
																	        ("facility_enchanting.png", 40, 40, (100, 100, 255, 255), "Ench"),
																		    ("facility_storage.png", 40, 40, (150, 100, 50, 255), "Box"),
																		        
																			    # 材料
																			        ("material_ore.png", 24, 24, (100, 100, 100, 255), "Ore"),
																				    ("material_herb.png", 24, 24, (50, 200, 50, 255), "Herb"),
																				        ("material_gem.png", 24, 24, (255, 50, 150, 255), "Gem"),
																					    ("material_essence.png", 24, 24, (0, 255, 255, 255), "Ess"),
																					    ]

																					    def create_placeholder_assets():
																					        output_dir = "game_assets"
																						    if not os.path.exists(output_dir):
																						            os.makedirs(output_dir)
																							            
																								        print(f"Generating assets in '{output_dir}/'...")
																									    
																									        for filename, width, height, color, text in assets_config:
																										        # 创建透明背景图片
																											        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
																												        draw = ImageDraw.Draw(img)
																													        
																														        # 绘制带边框的矩形
																															        draw.rectangle([0, 0, width-1, height-1], fill=color, outline=(255, 255, 255, 255))
																																        
																																	        # 尝试绘制简单的文字标识 (如果尺寸太小可能看不清，主要靠颜色区分)
																																		        if width > 20: 
																																			            # 简单的居中绘制逻辑
																																				                # 注意：实际项目中通常加载ttf字体，这里为了兼容性只画简单的线条或略过复杂文字
																																						            # 这里我们只画一个中心点或者首字母来表示方向
																																							                draw.text((width/2-5, height/2-5), text[0], fill=(255,255,255,255))
																																									            
																																										            file_path = os.path.join(output_dir, filename)
																																											            img.save(file_path, "PNG")
																																												            print(f"Created: {filename}")

																																													    if __name__ == "__main__":
																																													        create_placeholder_assets()
																																														    print("All assets generated successfully!")
