PREFIX := BiliScript
# 定义检查步骤
check:
	@if [ ! -f "tool/runtime/python.exe" ]; then \
		echo -e "缺少目标位置：找不到 \033[32mtool/runtime/python.exe\033[0"; \
		exit 1; \
	fi
	@if [ ! -f "tool/ffmpeg/ffmpeg.exe" ]; then \
		echo -e "缺少目标位置：找不到 \033[32mtool/ffmpeg/ffmpeg.exe\033[0"; \
		exit 1; \
	fi
	@echo -e "\033[32m所有必要文件已检查完毕。\033[0m"
	@if [ -d "runtime" ]; then \
		echo -e "检测到当前目录已存在 runtime 目录，请先运行 \033[32mmake clean\033[0m"; \
		exit 1; \
	fi

# 定义生成 requirement.txt 的目标
requirement:
	uv export -q -o requirement.txt
	@echo -e "requirement.txt 已生成。"

# 定义构建目标
build: check
	@echo -e "开始处理文件。"
	# 复制 tool/runtime 文件夹到当前目录
	@cp -r tool/runtime ./runtime
	@echo -e "tool/runtime 文件夹已复制到当前目录。"
	# 复制 tool/ffmpeg 下所有文件到 runtime 目录
	@cp tool/ffmpeg/* ./runtime/
	@echo -e "tool/ffmpeg 下的文件已复制到 runtime 目录。"
	# 执行 runtime/python.exe -m pip install -r tool/requirement.txt

	# @runtime/python.exe -m pip install -r tool/requirement.txt
	# @echo -e "\033[32m依赖已成功安装。\033[0m"

	# 执行依赖安装，带重试机制
	@$(MAKE) pip

# 定义重试安装依赖的目标
pip:
	@uv export -q -o tool/requirement.txt
	@max_retries=3; \
	count=0; \
	while [ $$count -le $$max_retries ]; do \
		if runtime/python.exe -m pip install -r tool/requirement.txt; then \
			echo -e "\033[32m依赖已成功安装。\033[0m"; \
			rm -f tool/requirement.txt; \
			exit 0; \
		else \
			echo -e "\033[33m依赖安装失败\033[0m，已重试 $$count 次。"; \
			count=$$((count + 1)); \
		fi; \
	done; \
	echo -e "\033[31m依赖安装失败\033[0m，网络可能需要魔法。"; \
	exit 1

package:
	@{ git ls-files -co --exclude-standard; echo "runtime/"; } > tool/filelist.txt
	@if [ ! -s tool/filelist.txt ]; then \
		echo -e "\033[31m错误：文件列表为空，没有可以压缩的内容。\033[0m"; \
		rm -f tool/filelist.txt; \
		exit 1; \
	fi
	@7z a tool/$(PREFIX).$(shell date +"%Y-%m-%dT%H-%M-%S").7z @tool/filelist.txt
	rm -f tool/filelist.txt
	@echo -e "\033[32m压缩完成，压缩文件存放在 tool 文件夹中。\033[0m"


clean:
	@rm -rf runtime
	@echo -e "\033[32mruntime 目录已清理。\033[0m"